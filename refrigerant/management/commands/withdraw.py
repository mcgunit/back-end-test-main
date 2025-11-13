from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import Vessel
import threading


class Command(BaseCommand):
    help = "Simulate condition when withdrawing refrigerant from a vessel."

    def handle(self, *args, **kwargs):
        # If vessel with id 1 exists do not just create another one. Instead lets make 3 vessels we can use in this simulation.
        # As if a company has 3 vessels in stock
        Vessel.objects.get_or_create(id=1, defaults={"name": f"Vessel_{1}", "content": 50.0})
        Vessel.objects.get_or_create(id=2, defaults={"name": f"Vessel_{2}", "content": 50.0})
        Vessel.objects.get_or_create(id=3, defaults={"name": f"Vessel_{3}", "content": 50.0})
        
        self.stdout.write("Simulating condition...")
        self.run_simulation()
        
    def doWithdraw(self, contentToWithdraw=10, user=" "):
        """
            Function to do a withdraw. Check the available vessels and notify user if empty or not enough available. 
        """
        with transaction.atomic():
            # Lock all vessels that have content > 0
            vessels = (
                Vessel.objects.select_for_update()
                .filter(content__gt=0)
                .order_by("id")
            )

            if not vessels.exists():
                self.stdout.write(f"For {user} no vessels with content found. Please order new vessels.")
                return

            for vessel in vessels:
                if vessel.content >= contentToWithdraw:
                    vessel.content -= contentToWithdraw
                    vessel.save()
                    self.stdout.write( f"{user} withdrew {contentToWithdraw} kg from {vessel.name}. Remaining: {vessel.content} kg")
                    return
                else:
                    used = vessel.content
                    vessel.content = 0
                    vessel.save()
                    self.stdout.write(f"For {user} vessel {vessel.name} ran out ({used} kg withdrawn), using the next vessel.")
                    contentToWithdraw -= used 

            if contentToWithdraw > 0:
                self.stdout.write(f"For {user} the vessels ran out of content. Please order new vessels")
                

    def run_simulation(self):
        barrier = threading.Barrier(2)

        def user1():
            barrier.wait()
            self.doWithdraw(contentToWithdraw=10, user="user1")
            
                    
        def user2():
            barrier.wait()
            self.doWithdraw(contentToWithdraw=13, user="user2")

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


        for vessel in Vessel.objects.all():
            self.stdout.write(f"Remaining content for {vessel.name}: {vessel.content} kg")

