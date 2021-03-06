import json
from decimal import *

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, generics, status, viewsets, filters
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from callback_functions.transfer_callback import transfer_callback
from .serializer import *


class RegisterView(generics.CreateAPIView):
    """
    Create User
    """
    permission_classes = (permissions.AllowAny,)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @transaction.atomic
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.id)


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class EthAccountViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EthAccountSerializer

    def get_queryset(self):
        return EthAccount.objects.filter(user=self.request.user)

    @detail_route()
    def get_balance(self, request, pk=None):
        eth_account = get_object_or_404(EthAccount, address=pk)
        address = pk

        # Get UTCoin balance
        num_suffix = 1000
        w3 = Web3(HTTPProvider(settings.WEB3_PROVIDER))
        eth_balance = w3.fromWei(w3.eth.getBalance(address), 'ether')
        abi = self.load_abi(settings.ARTIFACT_PATH)
        UTCoin = w3.eth.contract(abi=abi, address=settings.UTCOIN_ADDRESS)
        balance_int = UTCoin.call().balanceOf(address)
        balance = float(balance_int / num_suffix)

        context = {
            'address': address,
            'eth_balance': eth_balance,
            'balance': balance,
            'balance_int': balance_int
        }
        return Response(context)

    @detail_route()
    def get_qrcode(self, request, pk=None):
        eth_account = get_object_or_404(EthAccount, address=pk)
        address = pk
        eth_qrcode = eth_account.qrcode

        if not eth_qrcode:
            # Generate QR code
            img = qrcode.make(address)
            file_name = address + '.png'
            file_path = '/images/qrcode/' + file_name
            img.save(settings.MEDIA_ROOT + file_path)
            eth_account.qrcode = file_path
            eth_account.save()
            eth_qrcode = eth_account.qrcode

        context = {
            'address': address,
            'qrcode_url': eth_qrcode.url
        }
        return Response(context)

    @staticmethod
    def load_abi(file_path):
        """
        :param str file_path:
        :return dict: abi
        """
        artifact = open(file_path, 'r')
        json_dict = json.load(artifact)
        abi = json_dict['abi']
        return abi


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TransactionSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('from_address', 'to_address', 'amount', 'is_active', 'created_at')
    ordering_fields = ('id', 'amount', 'created_at')

    def get_queryset(self):
        address = self.request.user.account.address
        return Transaction.objects.filter(Q(from_address=address) | Q(to_address=address))

    @list_route(methods=['post'])
    @transaction.atomic
    def transfer(self, request):
        from_account = request.user.account

        # Receive params
        body = json.loads(request.body)
        to_address = body['address']
        amount = body['amount']
        if not (to_address and amount):
            error_msg = 'アドレスまたは金額が入力されていません。'
            print('Error:', error_msg)
            context = {
                'success': False,
                'detail': error_msg
            }
            return Response(context)

        # Validate address
        if not self.is_ut_address(to_address):
            error_msg = '無効なアドレスです。'
            print('Error:', error_msg)
            context = {
                'success': False,
                'detail': error_msg
            }
            return Response(context)

        amount = Decimal(amount)
        to_account = Account.objects.get(address=to_address)

        # Validate amount
        if from_account.balance < amount:
            error_msg = '送金可能額を超えています。'
            print('Error:', error_msg)
            context = {
                'success': False,
                'detail': error_msg
            }
            return Response(context)

        # UTCoin 送金
        with transaction.atomic():
            from_account.balance -= amount
            to_account.balance += amount
            from_account.save()
            to_account.save()

            # Create Transaction
            tx = Transaction.objects.create(
                from_address=from_account.address,
                to_address=to_address,
                amount=amount
            )

        # TODO: コントラクト実行
        # try:
        #     transfer_callback(tx_hash, from_address, to_address, amount_int, amount)
        # except Exception as e:
        #     print(e)
        #     error_msg = 'コールバック処理に失敗しました。'
        #     print('Error:', error_msg)
        #
        # else:
        #     error_msg = 'アカウントのアンロックに失敗しました。'
        #     print('Error:', error_msg)
        #     context = {
        #         'success': False,
        #         'detail': error_msg
        #     }
        #     return Response(context)

        context = {
            'success': True,
            'transaction': TransactionSerializer(tx).data
        }
        return Response(context, status=status.HTTP_201_CREATED)

    @staticmethod
    def is_ut_address(address):
        """
        :param str address:
        :return bool:
        """
        if address[0:2] == 'UT' and len(address) == 42:
            if Account.objects.filter(address=address).exists():
                return True
        return False


class EthTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EthTransactionSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = (
        'tx_hash', 'from_address', 'to_address', 'amount', 'gas', 'gas_price', 'value', 'network_id', 'is_active',
        'created_at')
    ordering_fields = ('id', 'amount', 'gas', 'gas_price', 'value', 'created_at')

    def get_queryset(self):
        eth_account = get_object_or_404(EthAccount, user=self.request.user)
        address = eth_account.address
        return EthTransaction.objects.filter(Q(from_address=address) | Q(to_address=address))

    @list_route(methods=['post'])
    @transaction.atomic
    def transfer(self, request):
        eth_account = get_object_or_404(EthAccount, user=request.user)
        from_address = eth_account.address
        num_suffix = 1000
        amount_min = 1 / num_suffix
        fee = 0.001

        # Receive params
        body = json.loads(request.body)
        to_address = body['address']
        amount = body['amount']
        if not (to_address and amount):
            error_msg = 'アドレスまたは金額が入力されていません。'
            print('Error:', error_msg)
            context = {
                'success': False,
                'detail': error_msg
            }
            return Response(context)

        amount = float(amount)
        amount_int = int(amount * num_suffix)

        # Validate address
        w3 = Web3(HTTPProvider(settings.WEB3_PROVIDER))
        if not w3.isAddress(to_address):
            error_msg = '無効なアドレスです。'
            print('Error:', error_msg)
            context = {
                'success': False,
                'detail': error_msg
            }
            return Response(context)

        # Validate amount
        if amount < amount_min:
            error_msg = '金額が不正です。'
            print('Error:', error_msg)
            context = {
                'success': False,
                'detail': error_msg
            }
            return Response(context)

        # Get UTCoin balance
        abi = self.load_abi(settings.ARTIFACT_PATH)
        UTCoin = w3.eadth.contract(abi=abi, address=settings.UTCOIN_ADDRESS)
        balance = UTCoin.call().balanceOf(from_address)

        if balance < amount + fee:
            error_msg = '残高が不足しています。'
            print('Error:', error_msg)
            context = {
                'success': False,
                'detail': error_msg
            }
            return Response(context)

        # Transfer UTCoin
        if w3.personal.unlockAccount(from_address, eth_account.password, duration=hex(300)):
            try:
                tx_hash = UTCoin.transact({'from': from_address}).transfer(to_address, amount_int)

                # Create Transaction
                transaction_info = w3.eth.getTransaction(tx_hash)
                Transaction.objects.create(
                    tx_hash=tx_hash,
                    from_address=from_address,
                    to_address=to_address,
                    amount=amount_int,
                    gas=transaction_info['gas'],
                    gas_price=transaction_info['gasPrice'],
                    value=transaction_info['value'],
                    network_id=transaction_info['networkId']
                )
            except Exception as e:
                print(e)
                error_msg = 'トランザクションに失敗しました。'
                print('Error:', error_msg)
                context = {
                    'success': False,
                    'detail': error_msg
                }
                return Response(context)

            # Execute callback function
            try:
                transfer_callback(tx_hash, from_address, to_address, amount_int, amount)
            except Exception as e:
                print(e)
                error_msg = 'コールバック処理に失敗しました。'
                print('Error:', error_msg)

        else:
            error_msg = 'アカウントのアンロックに失敗しました。'
            print('Error:', error_msg)
            context = {
                'success': False,
                'detail': error_msg
            }
            return Response(context)

        context = {
            'success': True,
            'address': to_address,
            'amount': amount,
            'fee': fee,
            'transaction': TransactionSerializer(transaction).data
        }
        return Response(context, status=status.HTTP_201_CREATED)

    @staticmethod
    def load_abi(file_path):
        """
        :param str file_path:
        :return dict: abi
        """
        artifact = open(file_path, 'r')
        json_dict = json.load(artifact)
        abi = json_dict['abi']
        return abi


class ContractViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ContractSerializer
    queryset = Contract.objects.all()

    def list(self, request):
        queryset = Contract.objects.filter(user=self.request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Contract.objects.all()
        contract = get_object_or_404(queryset, address=pk)
        serializer = ContractSerializer(contract)
        return Response(serializer.data)
