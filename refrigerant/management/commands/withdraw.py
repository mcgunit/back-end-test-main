from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import Vessel
import threading


class Command(BaseCommand):
    help = "Simulate condition when withdrawing refrigerant from a vessel."

    def handle(self, *args, **kwargs):
        Vessel.objects.create(name="Test Vessel", content=50.0)
        self.stdout.write("Simulating condition...")
        self.run_simulation()

    def run_simulation(self):
        barrier = threading.Barrier(2)

        def user1():
            barrier.wait()
            with transaction.atomic():
                vessel = Vessel.objects.select_for_update().get(id=1)
                if vessel.content <= 0:
                    self.stdout.write(f"User 1. The vessel you are currently withdrawal from is empty")
                else:
                    vessel.content -= 10.0
                    vessel.save()

        def user2():
            barrier.wait()
            with transaction.atomic():
                vessel = Vessel.objects.select_for_update().get(id=1)
                if vessel.content <= 0:
                    self.stdout.write(f"User 2. The vessel you are currently withdrawal from is empty")
                else:
                    vessel.content -= 10.0
                    vessel.save()

        """
            The problem here is that this will cause a race condition. 
            Because user 1 and 2 are almost reading at the same time the value.
            So basically with select_for_update() when one user is reading it creates a row lock so the others needs to wait
        """
        t1 = threading.Thread(target=user1)
        t2 = threading.Thread(target=user2)
        t1.start()
        t2.start()
        t1.join()
        t2.join()


        vessel = Vessel.objects.get(id=1)
        self.stdout.write(f"Remaining content: {vessel.content} kg")
