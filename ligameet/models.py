from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from PIL import Image
from django.core.validators import MinValueValidator 
from django.db.models import Q
from datetime import date
from django.utils.timezone import now

class Sport(models.Model):
    SPORT_NAME = models.CharField(max_length=100)
    SPORT_RULES_AND_REGULATIONS = models.TextField()
    EDITED_AT = models.DateTimeField(default=timezone.now)
    IMAGE = models.ImageField(upload_to='sports_icon/', null=True, blank=True)
    
    def __str__(self):
        return self.SPORT_NAME
    
    def get_recent_matches(self, limit=5):
        from .models import MatchDetails  # Import here to avoid circular import
        
        # Get matches for this sport
        matches = MatchDetails.objects.filter(
            Q(team1__SPORT_ID=self) & Q(team2__SPORT_ID=self)
        ).select_related('team1', 'team2', 'match')
        
        # Order by most recent and limit results
        recent_matches = matches.order_by('-match__MATCH_DATE')[:limit]
        
        return recent_matches
    
class Team(models.Model):
    TEAM_NAME = models.CharField(max_length=100)
    TEAM_TYPE = models.CharField(max_length=50) #junior senior, midget
    SPORT_ID = models.ForeignKey(Sport, on_delete=models.CASCADE)   
    COACH_ID = models.ForeignKey(User, on_delete=models.CASCADE)
    TEAM_LOGO = models.ImageField(upload_to='team_logo_images/', null=True, blank=True) 
    TEAM_DESCRIPTION = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.TEAM_NAME
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.TEAM_LOGO:  # Check if an image is associated   
            img = Image.open(self.TEAM_LOGO.path)
            try:
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.TEAM_LOGO.path)
            except Exception as e:
                print(f"Error processing image: {e}")



class Event(models.Model):
    STATUS_CHOICES = (
        ('Draft', 'Draft'),
        ('open', 'Open For Registration'),
        ('ongoing', 'Ongoing'),
        ('finished', 'Finished'),  
        ('cancelled', 'Cancelled'), 
    )
    EVENT_NAME = models.CharField(max_length=100)
    EVENT_DATE_START = models.DateTimeField()
    EVENT_DATE_END = models.DateTimeField() 
    EVENT_LOCATION = models.CharField(max_length=255)
    EVENT_STATUS = models.CharField(max_length=21, choices=STATUS_CHOICES, default='Draft')
    EVENT_ORGANIZER = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    EVENT_IMAGE = models.ImageField(upload_to='event_images/', null=True, blank=True) 
    SPORT = models.ManyToManyField(Sport, related_name='events')  
    PAYMENT_FEE = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    IS_SPONSORED = models.BooleanField(default=False)
    IS_POSTED = models.BooleanField(default=False) 
    CONTACT_PERSON = models.CharField(max_length=100, null=True, blank=True) 
    CONTACT_PHONE = models.CharField(max_length=15, null=True, blank=True)
    REGISTRATION_DEADLINE = models.DateTimeField() 
    teams = models.ManyToManyField(Team, through='TeamEvent', related_name='events')

    def __str__(self):
        sports_names = ', '.join(sport.SPORT_NAME for sport in self.SPORT.all())
        return f"{self.EVENT_NAME} - {sports_names}"
        

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.EVENT_IMAGE:  # Check if an image is associated
            img = Image.open(self.EVENT_IMAGE.path)

            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.EVENT_IMAGE.path)



    def transfer_money_to_organizer(self):
        """Transfers 80% of the total registration fees collected (based on SportDetails.entrance_fee) to the organizer's wallet."""
        if self.EVENT_STATUS == 'finished':
            print(f"Transfer method triggered for event: {self.EVENT_NAME}")

            # Initialize total collected fees
            total_collected_fees = Decimal('0.0')

            # Iterate through all team categories linked to the event
            for team_category in self.team_categories.all():
                # Access the SportDetails for the team category
                sport_details = team_category.sport_details.first()

                if sport_details:
                    # Calculate the total collected fees for this team category
                    entrance_fee = sport_details.entrance_fee
                    teams_registered = sport_details.teams.count()  # Number of teams registered for this sport
                    total_collected_fees += entrance_fee * Decimal(teams_registered)

                    print(
                        f"Team Category: {team_category.name}, Sport: {team_category.sport.SPORT_NAME}, "
                        f"Entrance Fee: {entrance_fee}, Teams Registered: {teams_registered}"
                    )

            if total_collected_fees <= 0:
                print(f"No money to transfer for event: {self.EVENT_NAME}")
                return

            # Calculate 80% of the total collected fees
            amount_to_transfer = total_collected_fees * Decimal('0.8')
            print(f"Amount to Transfer: {amount_to_transfer}")

            try:
                # Access the wallet of the event organizer
                organizer_wallet = Wallet.objects.get(user=self.EVENT_ORGANIZER)
                print(f"Current Wallet Balance: {organizer_wallet.WALLET_BALANCE}")

                # Update the wallet balance
                organizer_wallet.WALLET_BALANCE += amount_to_transfer
                organizer_wallet.save()

                print(f"New Wallet Balance: {organizer_wallet.WALLET_BALANCE}")
            except Wallet.DoesNotExist:
                print(f"Error: Wallet for {self.EVENT_ORGANIZER.username} does not exist.")



    def update_status(self):
        now = timezone.now()
        today = now.date()
        

        # Ensure self.EVENT_DATE_START is timezone-aware
        if timezone.is_naive(self.EVENT_DATE_START):
            self.EVENT_DATE_START = timezone.make_aware(self.EVENT_DATE_START, timezone.get_current_timezone())

        event_start_local = timezone.localtime(self.EVENT_DATE_START)
        

        # Do nothing if the event status is 'Draft' or 'cancelled'
        if self.EVENT_STATUS in ['draft', 'cancelled']:
            
            return

        # If the event has ended
        if self.EVENT_DATE_END < now:
            if self.EVENT_STATUS != 'finished':
                self.EVENT_STATUS = 'finished'
                self.save()  # Save status change
                self.transfer_money_to_organizer()  # Transfer money only when status changes
                
            return

        # Check if all sports in the event meet the required number of teams
        all_sports_ready = True
        for sport_detail in SportDetails.objects.filter(team_category__event=self):
            teams_registered = sport_detail.teams.count()
            
            if teams_registered < sport_detail.number_of_teams:
                all_sports_ready = False
                
                break

        # New conditions for registration deadline and status
        if all_sports_ready and event_start_local.date() > today:
            if self.REGISTRATION_DEADLINE > now:
                self.EVENT_STATUS = 'open'
                
            elif self.REGISTRATION_DEADLINE <= now:
                self.EVENT_STATUS = 'upcoming'
                

        # If all sports are ready and the event's start date has passed or is today, set status to 'ongoing'
        elif all_sports_ready and event_start_local.date() <= today:
            self.EVENT_STATUS = 'ongoing'
            


        self.save()
        













        
class TeamEvent(models.Model):
    TEAM_ID = models.ForeignKey(Team, on_delete=models.CASCADE)
    EVENT_ID = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['TEAM_ID', 'EVENT_ID'], name='unique_team_event')
        ]

    def __str__(self):
        return f"Team: {self.TEAM_ID.TEAM_NAME} - Event: {self.EVENT_ID.EVENT_NAME}"
    
class TeamCategory(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='team_categories', null=True, blank=True)  # Foreign key to Event
    name = models.CharField(max_length=50, null=True, blank=True)  # E.g., 'Junior', 'Senior', 'Midget'

    def __str__(self):
        return f"{self.name} - {self.sport} ({self.event.EVENT_NAME})"

class SportDetails(models.Model):
    team_category = models.ForeignKey(TeamCategory, on_delete=models.CASCADE, related_name='sport_details')  # Link to TeamCategory
    number_of_teams = models.PositiveIntegerField(default=0)  # Total number of teams allowed for this sport in the event
    players_per_team = models.PositiveIntegerField(default=0)  # Number of players per team for this sport in the event
    entrance_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)],
        help_text="Entrance fee should be greater than or equal to 0."
    )  # Entrance fee (should be >= 0)
    teams = models.ManyToManyField(Team, related_name='sport_details', blank=True)  # Teams registered for this sport in the event

    def __str__(self):
        return f"{self.team_category.name} - {self.team_category.sport.SPORT_NAME} ({self.team_category.event.EVENT_NAME})"

class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # The individual registering (optional for team registrations)
    coach = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='team_invoices')  # The coach registering the team
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)  # The team being registered (optional for individual registrations)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)  # The event being registered
    team_category = models.ForeignKey(TeamCategory, on_delete=models.CASCADE)  # Sport category in the event
    created_at = models.DateTimeField(auto_now_add=True)  # When the invoice was created
    is_paid = models.BooleanField(default=False)  # To track if payment has been made
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Registration amount

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['team', 'event', 'team_category'], name='unique_team_event_registration'),
            models.UniqueConstraint(fields=['user', 'event', 'team_category'], name='unique_user_event_registration'),
        ]

    def __str__(self):
        if self.team:
            return f"Invoice for Team {self.team.TEAM_NAME} - {self.event.EVENT_NAME} ({self.team_category.name})"
        elif self.user:
            return f"Invoice for {self.user.username} - {self.event.EVENT_NAME} ({self.team_category.name})"
        else:
            return f"Invoice for {self.event.EVENT_NAME} ({self.team_category.name})"

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    WALLET_BALANCE = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user} - {self.WALLET_BALANCE}"

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('refund', 'Refund'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        # Add other types as needed
    )
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.transaction_type} of {self.amount} to {self.wallet.user} on {self.created_at} - {self.description}"


class SportProfile(models.Model):  #TODO make a view to edit the sports he played
    USER_ID = models.ForeignKey(User, on_delete=models.CASCADE)
    SPORT_ID = models.ForeignKey(Sport, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['USER_ID', 'SPORT_ID'], name='unique_user_sport')
        ]

    def __str__(self):
        return f"{self.USER_ID.username} participating in {self.SPORT_ID.SPORT_NAME}"


class File(models.Model):
    USER_ID = models.ForeignKey(User, on_delete=models.CASCADE)
    FILE_PATH = models.FileField(upload_to='files/')

    def __str__(self):
        return str(self.FILE_PATH)



        
class TeamParticipant(models.Model):
    IS_CAPTAIN = models.BooleanField(default=False)
    USER_ID = models.ForeignKey(User, on_delete=models.CASCADE) #PART_ID
    TEAM_ID = models.ForeignKey(Team, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['USER_ID', 'TEAM_ID'], name='unique_team_user') # unique_team_participant
        ]

    def __str__(self):
        return f"{self.USER_ID} - {self.TEAM_ID}"
    

class Match(models.Model):
    team1 = models.CharField(max_length=100, null=True) #TODO remove all null true
    team2 = models.CharField(max_length=100, blank=True, null=True)
    round_number = models.IntegerField()  # Round of the match
    bracket_type = models.CharField(max_length=20, choices=[('WINNER', 'Winner Bracket'), ('LOSER', 'Loser Bracket')], null=True)
    team1_score = models.IntegerField(default=0)
    team2_score = models.IntegerField(default=0)
    schedule = models.DateTimeField() 

    def __str__(self):
        return f"Round {self.round_number}: {self.team1} vs {self.team2 or 'BYE'}"


class Subscription(models.Model):
    SUB_PLAN = models.CharField(max_length=50)
    SUB_DATE_STARTED = models.DateTimeField(default=timezone.now)
    SUB_DATE_END = models.DateTimeField()
    USER_ID = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.USER_ID.username} - {self.SUB_PLAN} (Started: {self.SUB_DATE_STARTED})"
    



class UserMatch(models.Model):
    MATCH_ID = models.ForeignKey(Match, on_delete=models.CASCADE)
    USER_ID = models.ForeignKey(User, on_delete=models.CASCADE)
    TEAM_ID = models.ForeignKey(Team, on_delete=models.CASCADE)
    IS_WINNER = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['MATCH_ID', 'USER_ID'], name='unique_user_match')
        ]

    def __str__(self):
        return f"Match: {self.MATCH_ID.MATCH_TYPE} - User: {self.USER_ID.username} - Team: {self.TEAM_ID.TEAM_NAME} - Winner: {self.IS_WINNER}"


class VolleyballStats(models.Model):
    VB_STATS_PT_COUNT = models.IntegerField(default=0)
    VB_STATS_ASSIST = models.IntegerField(default=0)
    VB_STATS_BLOCK = models.IntegerField(default=0)
    VB_STATS_ERROR = models.IntegerField(default=0)
    VB_STATS_IS_MVP = models.BooleanField(default=False)
    VB_STATS_SET = models.IntegerField(default=0)
    USER_ID = models.ForeignKey(User, on_delete=models.CASCADE)
    MATCH_ID = models.ForeignKey(Match, on_delete=models.CASCADE)
    USER_MATCH_ID = models.ForeignKey(UserMatch, on_delete=models.CASCADE)

    def __str__(self):
        return f"User: {self.USER_ID.username} - Match: {self.MATCH_ID.MATCH_TYPE} - MVP: {self.VB_STATS_IS_MVP}"


class UserRegistrationFee(models.Model):
    USER_MATCH_ID = models.ForeignKey(UserMatch, on_delete=models.CASCADE)
    IS_PAID = models.BooleanField(default=False)

    def __str__(self):
        return f"UserMatch: {self.USER_MATCH_ID} - Paid: {self.IS_PAID}"

class JoinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    USER_ID = models.ForeignKey(User, on_delete=models.CASCADE)
    TEAM_ID = models.ForeignKey(Team, on_delete=models.CASCADE)
    STATUS = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    REQUEST_DATE = models.DateTimeField(default=timezone.now)
        
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['USER_ID', 'TEAM_ID'], name='unique_join_request')
        ]

    def __str__(self):
        return f"{self.USER_ID.username} requesting to join {self.TEAM_ID.TEAM_NAME} - Status: {self.STATUS}"
    
class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Reference to the user
    description = models.TextField()  # Description of the activity
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set to the time of creation

    def __str__(self):
        return f"{self.user.username} - {self.description} on {self.timestamp}"

class Notification(models.Model):
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)  # recipient
    sender = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        user_username = self.user.username if self.user else 'Unknown'
        sender_username = self.sender.username if self.sender else 'Unknown'
        return f'Notification for {user_username} from {sender_username}: {self.message}'

    
class Invitation(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default='Pending')  # Status can be Pending, Accepted, Declined
    sent_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invitation to {self.user.username} for team {self.team.TEAM_NAME} - Status: {self.status}"
    

class PlayerRecruitment(models.Model):
    scout = models.ForeignKey(User, on_delete=models.CASCADE)
    player = models.ForeignKey(User, related_name='recruited_by', on_delete=models.CASCADE)
    is_recruited = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.scout.username} recruited {self.player.username}"

    

class BracketData(models.Model):
    sport_details = models.ForeignKey(SportDetails, on_delete=models.CASCADE, related_name="brackets",null=True)
    teams = models.JSONField()
    results = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bracket for {self.sport_details.team_category.event.EVENT_NAME} - {self.sport_details.team_category.name}"
    