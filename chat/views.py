import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Conversation, Message

@login_required
def chat_list_view(request):
    conversations = request.user.conversations.prefetch_related('participants', 'messages').all()
    conv_data = []
    for conv in conversations:
        other_user = conv.get_other_participant(request.user)
        if not other_user:
            continue
        last_message = conv.messages.order_by('-timestamp').first()
        unread_count = conv.messages.filter(is_read=False).exclude(sender=request.user).count()
        conv_data.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    return render(request, 'chat/chat_list.html', {'conversations': conv_data})

@login_required
def start_direct_chat_view(request, username):
    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        return redirect('chat_list')
    conv, _ = Conversation.get_or_create_direct_chat(request.user, target_user)
    return redirect('chat_room', room_id=conv.id)

@login_required
def chat_room_view(request, room_id):
    conversation = get_object_or_404(Conversation, id=room_id, participants=request.user)
    other_user = conversation.get_other_participant(request.user)
    if not other_user:
        return redirect('chat_list')
    
    # Mark messages as read on entry
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    messages = conversation.messages.select_related('sender', 'sender__profile').all()
    return render(request, 'chat/chat_room.html', {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages,
    })

@login_required
@require_POST
def upload_attachment_view(request, room_id):
    conversation = get_object_or_404(Conversation, id=room_id, participants=request.user)
    
    uploaded_file = request.FILES.get('attachment')
    text_content = request.POST.get('content', '').strip()

    if not uploaded_file:
        return JsonResponse({'status': 'error', 'error': 'No file uploaded.'}, status=400)

    max_size_mb = 15.0
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        return JsonResponse({'status': 'error', 'error': f'Attachment file size cannot exceed {max_size_mb}MB.'}, status=400)

    # Classify file type
    clean_filename = os.path.basename(uploaded_file.name)
    ext = os.path.splitext(clean_filename)[1].lower()
    msg_type = 'image' if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'] else 'file'

    # Save to database
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=text_content,
        message_type=msg_type,
        attachment=uploaded_file,
        attachment_name=clean_filename,
        attachment_size=uploaded_file.size
    )
    conversation.save()  # update conversation timestamp

    avatar_url = request.user.profile.avatar.url if hasattr(request.user, 'profile') and request.user.profile.avatar else ''

    message_payload = {
        'type': 'chat_message_event',
        'message_id': message.id,
        'content': message.content,
        'sender': request.user.username,
        'sender_avatar': avatar_url,
        'timestamp': message.timestamp.strftime('%I:%M %p'),
        'message_type': message.message_type,
        'attachment_url': message.attachment.url if message.attachment else '',
        'attachment_name': message.attachment_name,
        'attachment_size': message.formatted_size(),
    }

    # Broadcast to Channels group
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{conversation.id}',
        message_payload
    )

    return JsonResponse({
        'status': 'success',
        'message_id': message.id,
        'attachment_url': message.attachment.url,
        'attachment_name': message.attachment_name,
        'attachment_size': message.formatted_size(),
    })
