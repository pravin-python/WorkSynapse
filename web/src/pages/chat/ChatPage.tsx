/**
 * WorkSynapse Chat Page
 * =====================
 * Real-time messaging with channel selection.
 */
import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    MessageSquare,
    Hash,
    Lock,
    Users,
    Send,
    Smile,
    Paperclip,
    Search,
    MoreVertical,
    Phone,
    Video,
    Settings,
} from 'lucide-react';
import './Chat.css';

interface Channel {
    id: number;
    name: string;
    type: 'PUBLIC' | 'PRIVATE' | 'DIRECT';
    unread_count: number;
    last_message?: string;
    last_message_time?: string;
}

interface Message {
    id: number;
    content: string;
    sender_id: number;
    sender_name: string;
    sender_avatar?: string;
    timestamp: string;
    is_own: boolean;
}

export function ChatPage() {
    const { channelId } = useParams();
    const { user } = useAuth();
    const [channels, setChannels] = useState<Channel[]>([]);
    const [messages, setMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Load channels
        setChannels([
            { id: 1, name: 'general', type: 'PUBLIC', unread_count: 3, last_message: 'Hey team!', last_message_time: '10:30 AM' },
            { id: 2, name: 'development', type: 'PUBLIC', unread_count: 0, last_message: 'PR merged', last_message_time: '9:15 AM' },
            { id: 3, name: 'design', type: 'PRIVATE', unread_count: 1, last_message: 'New mockups ready', last_message_time: 'Yesterday' },
            { id: 4, name: 'Sarah Chen', type: 'DIRECT', unread_count: 2, last_message: 'Thanks!', last_message_time: '2:45 PM' },
        ]);

        // Simulated messages
        setMessages([
            { id: 1, content: 'Good morning team! 👋', sender_id: 2, sender_name: 'Sarah Chen', timestamp: '10:30 AM', is_own: false },
            { id: 2, content: 'Morning! Ready for today\'s standup?', sender_id: 1, sender_name: 'Alex Johnson', timestamp: '10:31 AM', is_own: true },
            { id: 3, content: 'Yes! I\'ve got some updates on the dashboard', sender_id: 2, sender_name: 'Sarah Chen', timestamp: '10:32 AM', is_own: false },
            { id: 4, content: 'Great, let\'s do it at 11', sender_id: 3, sender_name: 'Mike Rivera', timestamp: '10:33 AM', is_own: false },
            { id: 5, content: 'Sounds good! 🎯', sender_id: 1, sender_name: 'Alex Johnson', timestamp: '10:34 AM', is_own: true },
        ]);

        setSelectedChannel(channels[0] || null);
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMessage.trim()) return;

        const message: Message = {
            id: messages.length + 1,
            content: newMessage,
            sender_id: 1,
            sender_name: 'Alex Johnson',
            timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
            is_own: true,
        };

        setMessages([...messages, message]);
        setNewMessage('');
    };

    const getChannelIcon = (type: string) => {
        switch (type) {
            case 'PRIVATE': return <Lock size={16} />;
            case 'DIRECT': return <Users size={16} />;
            default: return <Hash size={16} />;
        }
    };

    return (
        <div className="chat-page">
            {/* Channels Sidebar */}
            <aside className="chat-sidebar">
                <div className="sidebar-header">
                    <h2>Messages</h2>
                    <button className="btn-icon" title="New message">
                        <MessageSquare size={18} />
                    </button>
                </div>

                <div className="channel-search">
                    <Search size={16} />
                    <input type="text" placeholder="Search messages..." />
                </div>

                <div className="channels-list">
                    <div className="channel-section">
                        <h3>Channels</h3>
                        {channels.filter(c => c.type !== 'DIRECT').map((channel) => (
                            <button
                                key={channel.id}
                                className={`channel-item ${selectedChannel?.id === channel.id ? 'active' : ''}`}
                                onClick={() => setSelectedChannel(channel)}
                            >
                                {getChannelIcon(channel.type)}
                                <span className="channel-name">{channel.name}</span>
                                {channel.unread_count > 0 && (
                                    <span className="unread-badge">{channel.unread_count}</span>
                                )}
                            </button>
                        ))}
                    </div>

                    <div className="channel-section">
                        <h3>Direct Messages</h3>
                        {channels.filter(c => c.type === 'DIRECT').map((channel) => (
                            <button
                                key={channel.id}
                                className={`channel-item ${selectedChannel?.id === channel.id ? 'active' : ''}`}
                                onClick={() => setSelectedChannel(channel)}
                            >
                                <div className="dm-avatar">{channel.name[0]}</div>
                                <span className="channel-name">{channel.name}</span>
                                {channel.unread_count > 0 && (
                                    <span className="unread-badge">{channel.unread_count}</span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>
            </aside>

            {/* Chat Main Area */}
            <main className="chat-main">
                {/* Chat Header */}
                <header className="chat-header">
                    <div className="chat-info">
                        {selectedChannel && getChannelIcon(selectedChannel.type)}
                        <h2>{selectedChannel?.name || 'Select a channel'}</h2>
                    </div>
                    <div className="chat-actions">
                        <button className="btn-icon" title="Call">
                            <Phone size={18} />
                        </button>
                        <button className="btn-icon" title="Video">
                            <Video size={18} />
                        </button>
                        <button className="btn-icon" title="Settings">
                            <Settings size={18} />
                        </button>
                    </div>
                </header>

                {/* Messages */}
                <div className="messages-container">
                    {messages.map((message) => (
                        <div key={message.id} className={`message ${message.is_own ? 'own' : ''}`}>
                            {!message.is_own && (
                                <div className="message-avatar">
                                    {message.sender_name[0]}
                                </div>
                            )}
                            <div className="message-content">
                                {!message.is_own && (
                                    <span className="message-sender">{message.sender_name}</span>
                                )}
                                <div className="message-bubble">
                                    <p>{message.content}</p>
                                </div>
                                <span className="message-time">{message.timestamp}</span>
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                {/* Message Input */}
                <form className="message-form" onSubmit={handleSendMessage}>
                    <button type="button" className="btn-icon" title="Attach file">
                        <Paperclip size={18} />
                    </button>
                    <input
                        type="text"
                        placeholder="Type a message..."
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                    />
                    <button type="button" className="btn-icon" title="Emoji">
                        <Smile size={18} />
                    </button>
                    <button type="submit" className="btn btn-primary send-btn" disabled={!newMessage.trim()}>
                        <Send size={18} />
                    </button>
                </form>
            </main>
        </div>
    );
}

export default ChatPage;
