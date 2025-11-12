# banco_oo.py
from __future__ import annotations

from datetime import datetime
import textwrap
from abc import ABC, abstractmethod


# =========================
# Domínio (Clientes / Contas)
# =========================
class Cliente:
    def __init__(self, endereco: str):
        self.endereco = endereco
        self.contas: list[Conta] = []

    def realizar_transacao(self, conta: "Conta", transacao: "Transacao"):
        transacao.registrar(conta)

    def adicionar_conta(self, conta: "Conta"):
        self.contas.append(conta)


class PessoaFisica(Cliente):
    def __init__(self, nome: str, data_nascimento: str, cpf: str, endereco: str):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf


class Historico:
    def __init__(self):
        self._transacoes: list[dict] = []

    @property
    def transacoes(self) -> list[dict]:
        return self._transacoes

    def adicionar_transacao(self, transacao: "Transacao"):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )


class Conta:
    def __init__(self, numero: int, cliente: Cliente):
        self._saldo: float = 0.0
        self._numero: int = numero
        self._agencia: str = "0001"
        self._cliente: Cliente = cliente
        self._historico: Historico = Historico()

    @classmethod
    def nova_conta(cls, cliente: Cliente, numero: int) -> "Conta":
        return cls(numero, cliente)

    @property
    def saldo(self) -> float:
        return self._saldo

    @property
    def numero(self) -> int:
        return self._numero

    @property
    def agencia(self) -> str:
        return self._agencia

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def historico(self) -> Historico:
        return self._historico

    def sacar(self, valor: float) -> bool:
        excedeu_saldo = valor > self.saldo
        if excedeu_saldo:
            print("\n⛔️ Operação falhou! Você não tem saldo suficiente. ⛔️")
        elif valor > 0:
            self._saldo -= valor
            print("\n✅ Saque realizado com sucesso! ✅")
            return True
        else:
            print("\n⛔️ Operação falhou! O valor informado é inválido. ⛔️")
        return False

    def depositar(self, valor: float) -> bool:
        if valor > 0:
            self._saldo += valor
            print("\n══ Depósito realizado com sucesso! ══")
            return True
        print("\n𐄂𐄂 Operação falhou! O valor informado é inválido. 𐄂𐄂")
        return False

    def __str__(self) -> str:
        return (
            f"\nAgência:\t{self.agencia}\n"
            f"C/C:\t\t{self.numero}\n"
            f"Titular:\t{getattr(self.cliente, 'nome', '(sem nome)')}\n"
        )


class ContaCorrente(Conta):
    def __init__(self, numero: int, cliente: Cliente, limite: float = 500.0, limite_saques: int = 3):
        super().__init__(numero, cliente)
        self.limite = float(limite)
        self.limite_saques = int(limite_saques)

    @classmethod
    def nova_conta(cls, cliente: Cliente, numero: int, limite: float = 500.0, limite_saques: int = 3) -> "ContaCorrente":
        return cls(numero, cliente, limite, limite_saques)

    def sacar(self, valor: float) -> bool:
        numero_saques = len([t for t in self.historico.transacoes if t["tipo"] == Saque.__name__])
        excedeu_limite = valor > self.limite
        excedeu_saques = numero_saques >= self.limite_saques

        if excedeu_limite:
            print("\n@@ Operação falhou! O valor do saque excede o limite. @@")
            return False
        if excedeu_saques:
            print("\n@@ Operação falhou! Número máximo de saques excedido. @@")
            return False
        return super().sacar(valor)


# =========================
# Transações
# =========================
class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self) -> float:
        ...

    @abstractmethod
    def registrar(self, conta: Conta) -> None:
        ...


class Saque(Transacao):
    def __init__(self, valor: float):
        self._valor = float(valor)

    @property
    def valor(self) -> float:
        return self._valor

    def registrar(self, conta: Conta) -> None:
        sucesso_transacao = conta.sacar(self.valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)


class Deposito(Transacao):
    def __init__(self, valor: float):
        self._valor = float(valor)

    @property
    def valor(self) -> float:
        return self._valor

    def registrar(self, conta: Conta) -> None:
        sucesso_transacao = conta.depositar(self.valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)


# =========================
# Camada de Aplicação (CLI)
# =========================
def menu() -> str:
    opcoes = """
    ================ MENU ================
    [d]\tDepositar
    [s]\tSacar
    [e]\tExtrato
    [nc]\tNova conta
    [lc]\tListar contas
    [nu]\tNovo cliente
    [q]\tSair
    => """
    return input(textwrap.dedent(opcoes))


def exibir_extrato(clientes: list[PessoaFisica]):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    print("\n================ EXTRATO ================")
    transacoes = conta.historico.transacoes

    extrato = ""
    if not transacoes:
        extrato = "Não foram realizadas movimentações."
    else:
        for transacao in transacoes:
            extrato += f"{transacao['tipo']}:\n\tR$ {transacao['valor']:.2f}\n"

    print(extrato)
    print(f"\nSaldo:\tR$ {conta.saldo:.2f}")


def listar_contas(contas: list[Conta]):
    for conta in contas:
        print("=" * 100)
        print(textwrap.dedent(str(conta)))


def criar_cliente(clientes: list[PessoaFisica]):
    cpf = input("Informe o CPF (somente número): ")
    cliente = filtrar_cliente(cpf, clientes)

    if cliente:
        print("\n⚠️⚠️⚠️ Já existe cliente com esse CPF! ⚠️⚠️⚠️")
        return

    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    cliente = PessoaFisica(nome=nome, data_nascimento=data_nascimento, cpf=cpf, endereco=endereco)
    clientes.append(cliente)

    print("\n✅ Cliente criado com sucesso! ✅")


def criar_conta(numero_conta: int, clientes: list[PessoaFisica], contas: list[Conta]):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n⚠️ Cliente não encontrado, fluxo de criação de conta encerrado! ⚠️")
        return

    conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta)
    contas.append(conta)
    # seguindo exatamente o seu exemplo: adiciona direto à lista do cliente
    cliente.contas.append(conta)

    print("\n✅ Conta criada com sucesso! ✅")


# ==== Utilidades do CLI ====
def filtrar_cliente(cpf: str, clientes: list[PessoaFisica]) -> PessoaFisica | None:
    filtrados = [c for c in clientes if c.cpf == cpf]
    return filtrados[0] if filtrados else None


def recuperar_conta_cliente(cliente: PessoaFisica) -> Conta | None:
    if not cliente.contas:
        print('\n⚠️ Cliente não possui conta! ⚠️')
        return None
    # FIXME: não permite cliente escolher a conta
    return cliente.contas[0]


def depositar(clientes: list[PessoaFisica]):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    try:
        valor = float(input("Informe o valor do depósito: "))
    except ValueError:
        print("\n@@@ Valor inválido! @@@")
        return

    transacao = Deposito(valor)
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    cliente.realizar_transacao(conta, transacao)


def sacar(clientes: list[PessoaFisica]):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n𐐒 Cliente não encontrado! 𐐒")
        return

    try:
        valor = float(input("Informe o valor do saque: "))
    except ValueError:
        print("\n@@@ Valor inválido! @@@")
        return

    transacao = Saque(valor)
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    cliente.realizar_transacao(conta, transacao)


def main():
    clientes: list[PessoaFisica] = []
    contas: list[Conta] = []

    while True:
        opcao = menu()

        if opcao == "d":
            depositar(clientes)

        elif opcao == "s":
            sacar(clientes)

        elif opcao == "e":
            exibir_extrato(clientes)

        elif opcao == "nu":
            criar_cliente(clientes)

        elif opcao == "nc":
            numero_conta = len(contas) + 1
            criar_conta(numero_conta, clientes, contas)

        elif opcao == "lc":
            listar_contas(contas)

        elif opcao == "q":
            print("\nAté mais! 👋")
            break

        else:
            print("\nOperação inválida, por favor selecione novamente a opção desejada.")


if __name__ == "__main__":
    main()
