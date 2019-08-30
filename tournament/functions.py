import sys
import datetime
import random
from datetime import *
from time import *
from itertools import cycle
from tournament.models import Tournament, Game
from django.utils import timezone


def get_current_tournament():
    if Tournament.objects.exists():
        return Tournament.objects.latest('id')
    return None


def get_number_of_rounds(num_of_participants):
    if num_of_participants % 2 == 0:
        return 4
    else:
        return 2


def generate_games_subset(games, participants):
    tournament = get_current_tournament()
    random.shuffle(participants)
    number_of_participants = len(participants)
    games_subset = []

    for i in range(number_of_participants // 2):

        game = Game(tournament=tournament, id1=participants[i], id2=participants[number_of_participants - i - 1])

        if game not in games:
            games_subset.append(game)

    return games_subset


def number_of_games(games, p_id):
    number = 0
    for game in games:
        if game.id1 == p_id or game.id2 == p_id:
            number += 1
    return number


def games_per_person(games, participants):

    games_per_person_list = [number_of_games(games, p) for p in participants]
    return games_per_person_list


def games_number_is_equal(games, participants):

    if len(set(games_per_person(games, participants))) == 1:
        return True
    else:
        return False


def generate_games():
    tour = get_current_tournament()
    number_of_rounds = get_number_of_rounds(tour.number_of_participants())
    divider = 2
    games_number = tour.games_per_person
    participants = [i for i in range(1, tour.number_of_participants() + 1)]

    games = []
    rounds_counter = 0
    attempts_number = 50
    attempt = 0
    games_per_person_list = [0] * len(participants)
    step = 1

    while rounds_counter != number_of_rounds:

        # generate possible couples
        if games_number_is_equal(games, participants):
            games_subset = generate_games_subset(games, participants)
        else:
            min_games = min(games_per_person(games, participants))
            subset_participants = [p for p in participants if number_of_games(games, p) == min_games]

            if len(subset_participants) < divider:
                for p in participants:
                    if p not in subset_participants:
                        subset_participants.append(p)
                        if len(subset_participants) == divider:
                            break

            games_subset = generate_games_subset(games, subset_participants)

        games.extend(games_subset)
        random.shuffle(participants)

        # exit when everybody has the same number of games
        if games_number_is_equal(games, participants):
            rounds_counter += 1

        # start again if impossible to generate unique couples
        attempt += 1
        if attempt > attempts_number:
            participants = [i for i in range(1, tour.number_of_participants() + 1)]
            games = []
            rounds_counter = 0
            attempt = 0

    return games


def get_time(start_time):
    tournament = get_current_tournament()
    TIME_INTERVAL = tournament.game_duration
    # return str(datetime.strptime(start_time, '%H:%M') + timedelta(minutes=TIME_INTERVAL))[11:-3]
    t = datetime.combine(datetime(1,1,1), start_time) + TIME_INTERVAL
    return t.time()


def get_dates():
    tournament = get_current_tournament()
    START_DAY = tournament.start_date
    NUMBER_OF_DAYS = tournament.start_date_playoff - tournament.start_date
    NUMBER_OF_DAYS = NUMBER_OF_DAYS.days
    days = []

    i = 0
    day = START_DAY
    while i < NUMBER_OF_DAYS:

        i += 1
        day_str = day.strftime("%a")

        if "Sun" in day_str or "Sat" in day_str:
            day = day + timedelta(days=1)
            continue
        days.append(day)
        day = day + timedelta(days=1)

    return days


def players_this_day(games, day):
    participants = []
    for game in games:
        if game.game_date == day:
            participants.append(game.id1)
            participants.append(game.id2)

    return participants


def have_slot_for_game(games, game, day, max_games=1):

    players = [game.id1, game.id2]

    for player in players:
        if players_this_day(games, day).count(player) >= max_games:
            return False
    return True


def games_this_day(games_all, day):
    games = []
    for game in games_all:
        if game.game_date == day:
            games.append(game)

    return games


def last_game_time(games_all, day):
    games = games_this_day(games_all, day)
    try:
        games.sort(key=lambda g: datetime.combine(datetime(1,1,1), g.start_time))
    except:
        pass
    return games[-1].start_time


def initial_games_number(days_number):
    t = get_current_tournament()
    nop = t.number_of_participants()
    gpp = t.games_per_person
    if gpp % days_number == 0 and nop % 2 == 0:
        return gpp // days_number
    return gpp // days_number + 1


def generate_schedule(games):
    tournament = get_current_tournament()
    START_TIME = tournament.game_start_time

    days = get_dates()
    num_of_days = len(days)
    not_set_games = []

    for game in games:
        for i in range(num_of_days):
            if have_slot_for_game(games, game, days[i]):
                if len(games_this_day(games, days[i])) == 0:
                    game_time = START_TIME
                else:
                    game_time = get_time(last_game_time(games, days[i]))

                game.start_time = game_time
                game.game_date = days[i]
                break
            if i == num_of_days - 1:
                not_set_games.append(game)

    if len(not_set_games) == 0:
        for game in games:
            game.save()
        return True
    else:
        return False
