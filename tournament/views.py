# -*- coding: utf-8 -*-
from datetime import *
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from .models import Tournament, Participant, SetResult, Game
from .forms import RegisterForm, ResultForm, UserCreationForm
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from tournament.functions import generate_games, generate_schedule, get_current_tournament, split_games_by_days


def index(request):
    status_msg = {
        0: "Открыта регистрация на турнир",
        1: "Регистрация на турнир завершена",
        2: "Групповой этап",
        3: "Плей-офф",
        4: "Турнир завершён.",
        5: "Нет данных о турнирах",
    }
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        tournament_status = 5
    msg = status_msg[tournament_status]
    return render(request, 'tournament/index.html', locals())


def participants(request):
    tournament = get_current_tournament()
    tournament_status = tournament.get_status()
    if tournament_status in (0, 1, 2, 3):
        return render(request, 'tournament/participants.html', locals())
    else:
        return HttpResponse("<h2>Participants list is not available</h2>")


def games(request, game=None):
    tournament = get_current_tournament()
    tournament_status = tournament.get_status()
    games = tournament.game_set.filter(game_id=0).order_by('game_date', 'start_time')
    days = split_games_by_days(games)
    if tournament_status in (0, 1, 2, 3):
        return render(request, 'tournament/games.html', locals())
    else:
        return HttpResponse("<h2>Games list is not available</h2>")


def rating(request):
    tournament = get_current_tournament()
    tournament_status = tournament.get_status()
    for p in tournament.participant_set.all():
        p.win_sets = 0
        p.win_balls = 0
        p.games_left = 0
        for g in Game.objects.filter((Q(participant1=p) | Q(participant2=p)) & Q(game_id=0)):
            if g.setresult_set.exists():
                for r in g.setresult_set.all():
                    if g.participant1 == p:
                        if r.result1 > r.result2:
                            p.win_sets += 1
                        p.win_balls += r.result1 - r.result2
                    else:
                        if r.result2 > r.result1:
                            p.win_sets += 1
                        p.win_balls += r.result2 - r.result1
            else:
                p.games_left += 1
        p.save(update_fields=["win_sets", "win_balls", "games_left"])

    participants = list(tournament.participant_set.all())
    participants.sort(key=lambda elem: (elem.win_sets, elem.win_balls), reverse=True)

    if tournament_status in (0, 1, 2, 3):
        return render(request, 'tournament/rating.html', locals())
    else:
        return HttpResponse("<h2>Participants rating is not available</h2>")


def playoff(request):
    tournament = get_current_tournament()
    tournament_status = tournament.get_status()
    playoff_games = list(Game.objects.filter(Q(tournament=tournament) & ~Q(game_id=0)))
    if not playoff_games:
        for p in tournament.participant_set.all():
            p.win_sets = 0
            p.win_balls = 0
            p.games_left = 0
            for g in Game.objects.filter(Q(participant1=p) | Q(participant2=p)):
                if g.setresult_set.exists():
                    for r in g.setresult_set.all():
                        if g.participant1 == p:
                            if r.result1 > r.result2:
                                p.win_sets += 1
                            p.win_balls += r.result1 - r.result2
                        else:
                            if r.result2 > r.result1:
                                p.win_sets += 1
                            p.win_balls += r.result2 - r.result1
                else:
                    p.games_left += 1
            p.save(update_fields=["win_sets", "win_balls", "games_left"])

        participants = list(tournament.participant_set.all())
        participants.sort(key=lambda elem: (elem.win_sets, elem.win_balls), reverse=True)
        playoffs = participants[:8]

        for i in range(4):
            g = Game(tournament=tournament, game_id=i+1, id1=playoffs[i].drawn_number, id2=playoffs[7-i].drawn_number,
                     participant1=playoffs[i], participant2=playoffs[7-i],
                     game_date=tournament.start_date_playoff, start_time="1{}:00:00".format(i+2))
            g.save()

        semi_day = tournament.start_date_playoff + timedelta(days=1)
        for i in range(2):
            g = Game(tournament=tournament, game_id=i+5, id1=i+1, id2=4-i,
                     game_date=semi_day, start_time="1{}:00:00".format(i*2+3))
            g.save()

        final_day = tournament.start_date_playoff + timedelta(days=2)

        g = Game(tournament=tournament, game_id=7, id1=-5, id2=-6,
                 game_date=final_day, start_time="13:00:00")
        g.save()
        g = Game(tournament=tournament, game_id=8, id1=5, id2=6,
                 game_date=final_day, start_time="15:00:00")
        g.save()

    quarter_games = list(Game.objects.filter(Q(tournament=tournament) &
                                             (Q(game_id=1) | Q(game_id=2) |
                                              Q(game_id=3) | Q(game_id=4))))

    semi_games = list(Game.objects.filter(Q(tournament=tournament) &
                                          (Q(game_id=5) | Q(game_id=6))))

    for g in semi_games:
        if type(g.get_p1()) is not Participant:
            p1 = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=g.get_p1())))[0].get_winner()
            if p1:
                g.participant1 = p1
                g.save(first_call=False, update_fields=["participant1"])
        if type(g.get_p2()) is not Participant:
            p2 = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=g.get_p2())))[0].get_winner()
            if p2:
                g.participant2 = p2
                g.save(first_call=False, update_fields=["participant2"])

    third_game = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=7)))
    for g in third_game:
        if type(g.get_p1()) is not Participant:
            p1 = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=5)))[0].get_loser()
            if p1:
                g.participant1 = p1
                g.save(first_call=False, update_fields=["participant1"])
        if type(g.get_p2()) is not Participant:
            p2 = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=6)))[0].get_loser()
            if p2:
                g.participant2 = p2
                g.save(first_call=False, update_fields=["participant2"])

    final_game = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=8)))
    for g in final_game:
        if type(g.get_p1()) is not Participant:
            p1 = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=5)))[0].get_winner()
            if p1:
                g.participant1 = p1
                g.save(first_call=False, update_fields=["participant1"])
        if type(g.get_p2()) is not Participant:
            p2 = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=6)))[0].get_winner()
            if p2:
                g.participant2 = p2
                g.save(first_call=False, update_fields=["participant2"])

    if tournament_status in (0, 1, 2, 3):
        return render(request, 'tournament/playoff.html', locals())
    else:
        return HttpResponse("<h2>Play-off games are not available</h2>")


def account_register(request):

    tournament = get_current_tournament()
    tournament_status = tournament.get_status()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(username=form.cleaned_data['username'],
                                            email=form.cleaned_data['email'],
                                            first_name=form.cleaned_data['first_name'],
                                            last_name=form.cleaned_data['last_name'],
                                            password=form.cleaned_data['password1'])
            login(request, user)
            return HttpResponseRedirect('/accounts/me/')
    else:
        form = UserCreationForm()

    return render(request, 'auth/account_register.html', locals())


def account_login(request):

    tournament = get_current_tournament()
    tournament_status = tournament.get_status()

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(request,
                                username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            login(request, user)
            return HttpResponseRedirect('/accounts/me/')
    else:
        form = AuthenticationForm()

    form.fields["username"].widget.attrs["class"] = "form-control"
    form.fields["password"].widget.attrs["class"] = "form-control"
    return render(request, 'auth/account_login.html', locals())


def account_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


@login_required
def me(request, game=None):
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        tournament_status = 5

    # Registration is open
    if tournament_status == 0:
        return HttpResponseRedirect('/accounts/me/register/')
    # Registration is over
    elif tournament_status == 1:
        return HttpResponseRedirect('/accounts/me/before_draw/')
    # Group stage
    elif tournament_status == 2:
        return HttpResponseRedirect('/accounts/me/games/')
    # Play-off
    elif tournament_status == 3:
        pass
    # Tournament finished
    elif tournament_status == 4:
        pass
    else:
        pass

    return render(request, 'tournament/index.html', locals())


@login_required
def me_register(request):
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        tournament_status = 5

    if tournament_status == 0:
        if Participant.objects.filter(Q(tournament=tournament) & Q(user=request.user)):
            is_registered = True
        else:
            is_registered = False

        if request.method == 'POST':
            p = Participant(tournament=tournament,
                            user=request.user)
            p.save()
            return HttpResponseRedirect('/accounts/me/register/')

        return render(request, 'auth/me_register.html', locals())
    return HttpResponseRedirect('/accounts/me/')


@login_required
def me_before_draw(request):
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        tournament_status = 5

    if tournament_status == 1:
        if request.user.username == "admin":
            if tournament.game_set.all():
                games_generated = True
            else:
                games_generated = False
        else:
            return HttpResponseRedirect('/accounts/me/games/')

        if request.method == 'POST':
            schedule_ready = False
            while not schedule_ready:
                games = generate_games()
                schedule_ready = generate_schedule(games)
            return HttpResponseRedirect('/accounts/me/before_draw/')

        return render(request, 'auth/me_before_draw.html', locals())
    return HttpResponseRedirect('/accounts/me/')


@login_required
def me_games(request, game=None):
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        tournament_status = 5

    if tournament_status == 1 or tournament_status == 2:
        try:
            p = Participant.objects.get(Q(user=request.user) & Q(tournament=tournament))
        except ObjectDoesNotExist:
            return render(request, 'auth/me_games.html', locals())

        if not p.drawn_number:
            return render(request, 'auth/me_games.html', locals())

        games = tournament.game_set.filter(Q(participant1=p) | Q(participant2=p)).order_by('game_date', 'start_time')

        for g in games:
            g.form = ResultForm()

        if request.method == 'POST':
            game = Game.objects.get(pk=game)
            for g in games:
                if g == game:
                    g.form = ResultForm(request.POST)
                    if g.form.is_valid():
                        for i in range(1, 6):
                            s = SetResult(game=game,
                                          set_number=i,
                                          result1=g.form.cleaned_data['set{}res1'.format(i)],
                                          result2=g.form.cleaned_data['set{}res2'.format(i)])
                            s.save()
                        return HttpResponseRedirect('/accounts/me/games/')
                    break
        return render(request, 'auth/me_games.html', locals())
    return HttpResponseRedirect('/accounts/me/')
