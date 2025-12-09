# refactor_solid.py

from abc import ABC, abstractmethod
from dataclasses import dataclass


# =====================================================
# LANGKAH 1 : KODE BERMASALAH (The God Class)
# =====================================================

@dataclass
class Order:
    customer_name: str
    total_price: float
    status: str = "open"


class OrderManager:  # Melanggar SRP, OCP, DIP
    def process_checkout(self, order: Order, payment_method: str):
        print(f"Memulai checkout untuk {order.customer_name}...")

        # Logika pembayaran DI HARD-CODE (pelanggaran OCP & DIP)
        if payment_method == "credit_card":
            print("Processing Credit Card...")
        elif payment_method == "bank_transfer":
            print("Processing Bank Transfer...")
        else:
            print("Metode tidak valid.")
            return False

        # Logika notifikasi juga ditumpuk di sini (pelanggaran SRP)
        print(f"Mengirim notifikasi ke {order.customer_name}...")
        order.status = "paid"
        return True


# =====================================================
# LANGKAH 2 : REFACTORING → SRP + DIP + OCP
# =====================================================

# Interface Pembayaran (DIP)
class IPaymentProcessor(ABC):
    @abstractmethod
    def pay(self, order: Order) -> bool:
        pass


# Implementasi konkret (Credit Card)
class CreditCardPayment(IPaymentProcessor):
    def pay(self, order: Order) -> bool:
        print("Pembayaran menggunakan Kartu Kredit...")
        return True


# Implementasi konkret lain (Bank Transfer)
class BankTransferPayment(IPaymentProcessor):
    def pay(self, order: Order) -> bool:
        print("Pembayaran melalui Bank Transfer...")
        return True


# Service Notifikasi dipisah (SRP)
class NotificationService:
    def send(self, order: Order):
        print(f"🔔 Notifikasi terkirim ke {order.customer_name}")


# Coordinator class (OrderService) menerapkan DIP
class OrderService:
    def __init__(self, payment: IPaymentProcessor, notification: NotificationService):
        self.payment = payment
        self.notification = notification

    def checkout(self, order: Order):
        print(f"Checkout: {order.customer_name}")

        # Delegasi pembayaran ke Service yang DIINJEKSI
        if self.payment.pay(order):
            order.status = "paid"
            self.notification.send(order)
            return True
        return False


# =====================================================
# LANGKAH 3 : PEMBUKTIAN OCP
# =====================================================

if __name__ == "__main__":
    # Kita bisa ganti strategi pembayaran tanpa ubah kode OrderService ✔
    order = Order("Moja", 150000)

    payment_method = CreditCardPayment()   # Coba — dapat diganti BankTransferPayment()
    notification = NotificationService()

    app = OrderService(payment_method, notification)
    success = app.checkout(order)

    print("Status Order:", order.status)
