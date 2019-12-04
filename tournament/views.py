# -*- coding: utf-8 -*-
from datetime import *
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from .models import Tournament, Participant, SetResult, Game
from .forms import PlayoffResultForm, ResultForm, UserCreationForm
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from tournament.functions import generate_games, generate_schedule, get_current_tournament, split_games_by_days,\
    write_schedule_to_xls, generate_playoff_games, recount_rating


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
    if tournament:
        tournament_status = tournament.get_status()
    else:
        return HttpResponse("<h2>Participants list is not available</h2>")
    if tournament_status in (0, 1, 2, 3):
        return render(request, 'tournament/participants.html', locals())
    else:
        return HttpResponse("<h2>Participants list is not available</h2>")


def games(request, game=None):
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        return HttpResponse("<h2>Games list is not available</h2>")
    games = list(tournament.game_set.filter(game_id=0).order_by('game_date', 'start_time'))
    if games:
        days = split_games_by_days(games)
    if tournament_status in (0, 1, 2, 3):
        return render(request, 'tournament/games.html', locals())
    else:
        return HttpResponse("<h2>Games list is not available</h2>")


def rating(request):
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        return HttpResponse("<h2>Rating is not available</h2>")
    recount_rating()

    participants = list(tournament.participant_set.all())
    participants.sort(key=lambda elem: (elem.win_sets, elem.win_balls), reverse=True)

    if tournament_status in (0, 1, 2, 3):
        return render(request, 'tournament/rating.html', locals())
    else:
        return HttpResponse("<h2>Participants rating is not available</h2>")


def playoff(request):
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        return HttpResponse("<h2>Play-off games are not available</h2>")
    recount_rating()

    participants = list(tournament.participant_set.all())
    participants.sort(key=lambda elem: (elem.win_sets, elem.win_balls), reverse=True)
    playoffs = participants[:8]

    quarter_games = list(Game.objects.filter(Q(tournament=tournament) &
                                             (Q(game_id=1) | Q(game_id=2) |
                                              Q(game_id=3) | Q(game_id=4))))

    for g in quarter_games:
        g.participant1 = playoffs[g.id1 - 1]
        g.participant2 = playoffs[g.id2 - 1]
        g.save(first_call=False, update_fields=["participant1", "participant2"])

    semi_games = list(Game.objects.filter(Q(tournament=tournament) &
                                          (Q(game_id=5) | Q(game_id=6))))

    for g in semi_games:
        if type(g.get_p1()) is not Participant:
            p1 = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=g.id1)))[0].get_winner()
            if p1:
                g.participant1 = p1
                g.save(first_call=False, update_fields=["participant1"])
        if type(g.get_p2()) is not Participant:
            p2 = list(Game.objects.filter(Q(tournament=tournament) & Q(game_id=g.id2)))[0].get_winner()
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
        return HttpResponseRedirect('/accounts/me/playoff_games/')
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
                return HttpResponseRedirect('/accounts/me/after_draw/')
        else:
            return HttpResponseRedirect('/accounts/me/games/')

        if request.method == 'POST':
            schedule_ready = False
            while not schedule_ready:
                games = generate_games()
                schedule_ready = generate_schedule(games)
            generate_playoff_games()
            return HttpResponseRedirect('/accounts/me/before_draw/')

        return render(request, 'auth/me_before_draw.html', locals())
    return HttpResponseRedirect('/accounts/me/')


@login_required
def me_after_draw(request):
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        tournament_status = 5

    if tournament_status == 1:
        if request.user.username != "admin":
            return HttpResponseRedirect('/accounts/me/games/')

        if request.method == 'POST':
            games = tournament.game_set.filter(game_id=0).order_by('game_date', 'start_time')
            days = split_games_by_days(games)
            write_schedule_to_xls(days, tournament.number_of_sets)
            return HttpResponseRedirect('/accounts/me/after_draw/')

        return render(request, 'auth/me_after_draw.html', locals())
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

        games = tournament.game_set.filter(Q(game_id=0) &
                                           (Q(participant1=p) | Q(participant2=p))).order_by('game_date', 'start_time')

        for g in games:
            g.form = ResultForm()

        if request.method == 'POST':
            game = Game.objects.get(pk=game)
            for g in games:
                if g == game:
                    if g.setresult_set.exists():
                        return HttpResponseRedirect('/accounts/me/games/')
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


@login_required
def me_playoff_games(request, game=None):
    tournament = get_current_tournament()
    if tournament:
        tournament_status = tournament.get_status()
    else:
        tournament_status = 5

    if tournament_status == 3:
        try:
            p = Participant.objects.get(Q(user=request.user) & Q(tournament=tournament))
        except ObjectDoesNotExist:
            return render(request, 'auth/me_playoff_games.html', locals())

        games = tournament.game_set.filter(~Q(game_id=0) &
                                           (Q(participant1=p) | Q(participant2=p))).order_by('game_date', 'start_time')

        for g in games:
            g.form = PlayoffResultForm()

        if request.method == 'POST':
            game = Game.objects.get(pk=game)
            for g in games:
                if g == game:
                    if g.setresult_set.exists():
                        return HttpResponseRedirect('/accounts/me/playoff_games/')
                    g.form = PlayoffResultForm(request.POST)
                    if g.form.is_valid():
                        for i in range(1, 8):
                            if g.form.cleaned_data['set{}res1'.format(i)] is None:
                                break
                            s = SetResult(game=game,
                                          set_number=i,
                                          result1=g.form.cleaned_data['set{}res1'.format(i)],
                                          result2=g.form.cleaned_data['set{}res2'.format(i)])
                            s.save()
                        return HttpResponseRedirect('/accounts/me/playoff_games/')
                    break
        return render(request, 'auth/me_playoff_games.html', locals())
    return HttpResponseRedirect('/accounts/me/')
