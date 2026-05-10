from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Note
from .forms import NoteForm


@login_required
def notes_list(request):
    qs = Note.objects.filter(user=request.user)
    q = request.GET.get('q')
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(body__icontains=q)
    return render(request, 'notes/list.html', {'notes': qs, 'q': q or ''})


@login_required
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, user=request.user)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            messages.success(request, "Note saved.")
            return redirect('notes:list')
    else:
        form = NoteForm(user=request.user)
    return render(request, 'notes/form.html', {'form': form, 'is_new': True})


@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Note updated.")
            return redirect('notes:list')
    else:
        form = NoteForm(instance=note, user=request.user)
    return render(request, 'notes/form.html', {'form': form, 'is_new': False, 'note': note})


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        note.delete()
        messages.success(request, "Note deleted.")
        return redirect('notes:list')
    return render(request, 'notes/confirm_delete.html', {'note': note})
