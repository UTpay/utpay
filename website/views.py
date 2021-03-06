from decimal import *

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from accounts.models import Transaction, EthTransaction
from .forms import *


class IndexView(TemplateView):
    template_name = 'index.html'


@method_decorator(login_required, name='dispatch')
class TransferView(View):
    template_name = 'transfer.html'

    def get(self, request):
        form = self.init_form()

        context = {
            'title': 'コインを送る',
            'form': form
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = TransferForm(user=request.user, data=request.POST)
        if form.is_valid():
            to_address = form.cleaned_data['address']
            if self.is_ut_address(to_address):
                # UT address -> UT address
                from_account = request.user.account
                to_account = Account.objects.get(address=to_address)
                amount = Decimal(form.cleaned_data['amount'])

                # UTCoin 送金
                with transaction.atomic():
                    from_account.balance -= amount
                    to_account.balance += amount
                    from_account.save()
                    to_account.save()

                    # Create OffChainTransaction
                    Transaction.objects.create(
                        from_address=from_account.address,
                        to_address=to_address,
                        amount=amount
                    )

            else:
                # UT address -> ETH address
                num_suffix = 1000
                from_account = request.user.account
                admin = User.objects.get(pk=1)
                admin_eth_account = admin.ethaccount
                amount = int(form.cleaned_data['amount'] * num_suffix)
                fee = 0

                # UTCoin 送金
                w3 = Web3(HTTPProvider(settings.WEB3_PROVIDER))
                abi = self.load_abi(settings.ARTIFACT_PATH)
                UTCoin = w3.eth.contract(abi=abi, address=settings.UTCOIN_ADDRESS)
                if w3.personal.unlockAccount(admin_eth_account.address, admin_eth_account.password, duration=hex(60)):
                    try:
                        tx_hash = UTCoin.transact({'from': admin_eth_account.address}).transfer(to_address,
                                                                                                amount - fee)

                        with transaction.atomic():
                            from_account.balance -= amount
                            from_account.save()

                            # Create Transaction
                            tx_info = w3.eth.getTransaction(tx_hash)
                            EthTransaction.objects.create(
                                tx_hash=tx_hash,
                                from_address=admin_eth_account.address,
                                to_address=to_address,
                                amount=amount,
                                gas=tx_info['gas'],
                                gas_price=tx_info['gasPrice'],
                                value=tx_info['value'],
                                network_id=tx_info['networkId']
                            )
                    except Exception as e:
                        print(e)

                else:
                    print('failed to unlock account')

            # フォーム初期化 (送金可能額を再計算)
            form = self.init_form()

        context = {
            'title': 'コインを送る',
            'form': form
        }
        return render(request, self.template_name, context)

    def init_form(self, fee=0):
        """
        :param int fee:
        :return class 'website.forms.TransferForm':
        """
        account = self.request.user.account
        fee = str(fee)

        # 送金可能額を計算
        balance = account.balance - Decimal(fee)
        if balance < 0:
            balance = 0

        form = TransferForm(user=self.request.user, initial={'fee': fee, 'balance': balance})
        return form

    @staticmethod
    def is_ut_address(address: str) -> bool:
        """
        :param str address:
        :return bool:
        """
        if address[0:2] == 'UT' and len(address) == 42:
            if Account.objects.filter(address=address).exists():
                return True
        return False

    @staticmethod
    def load_abi(file_path: str):
        """
        :param str file_path:
        :return dict: abi
        """
        artifact = open(file_path, 'r')
        json_dict = json.load(artifact)
        abi = json_dict['abi']
        return abi
