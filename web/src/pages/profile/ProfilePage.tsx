/**
 * WorkSynapse Profile Page
 */
import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { User, Mail, Shield, Calendar, Edit, Camera } from 'lucide-react';
import './Profile.css';

export function ProfilePage() {
    const { user } = useAuth();

    return (
        <div className="profile-page">
            <header className="page-header">
                <h1><User size={28} />Profile</h1>
            </header>

            <div className="profile-content">
                <div className="profile-card">
                    <div className="profile-avatar">
                        <div className="avatar-large">
                            {user?.full_name?.[0] || 'U'}
                        </div>
                        <button className="avatar-edit"><Camera size={16} /></button>
                    </div>
                    <h2>{user?.full_name}</h2>
                    <p className="role-badge">{user?.role}</p>

                    <div className="profile-details">
                        <div className="detail-item">
                            <Mail size={18} />
                            <span>{user?.email}</span>
                        </div>
                        <div className="detail-item">
                            <Shield size={18} />
                            <span>Role: {user?.role}</span>
                        </div>
                        <div className="detail-item">
                            <Calendar size={18} />
                            <span>Member since: Jan 2024</span>
                        </div>
                    </div>

                    <button className="btn btn-secondary">
                        <Edit size={16} />
                        Edit Profile
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ProfilePage;
