/**
 * WorkSynapse Settings Page
 */
import React from 'react';
import { Settings, Bell, Lock, Palette, Globe, Database } from 'lucide-react';
import ThemeSwitcher from '../../components/ui/ThemeSwitcher';
import './Settings.css';

export function SettingsPage() {
    return (
        <div className="settings-page">
            <header className="page-header">
                <h1><Settings size={28} />Settings</h1>
                <p>Manage your account and preferences</p>
            </header>

            <div className="settings-grid">
                <section className="settings-section">
                    <h2><Palette size={20} />Appearance</h2>
                    <p>Customize the look and feel of your workspace</p>
                    <ThemeSwitcher variant="full" />
                </section>

                <section className="settings-section">
                    <h2><Bell size={20} />Notifications</h2>
                    <p>Configure how you receive notifications</p>
                    <div className="setting-item">
                        <div className="setting-info">
                            <span>Email Notifications</span>
                            <span className="setting-desc">Receive email for important updates</span>
                        </div>
                        <label className="toggle">
                            <input type="checkbox" defaultChecked />
                            <span className="toggle-slider"></span>
                        </label>
                    </div>
                    <div className="setting-item">
                        <div className="setting-info">
                            <span>Push Notifications</span>
                            <span className="setting-desc">Browser push notifications</span>
                        </div>
                        <label className="toggle">
                            <input type="checkbox" />
                            <span className="toggle-slider"></span>
                        </label>
                    </div>
                </section>

                <section className="settings-section">
                    <h2><Lock size={20} />Security</h2>
                    <p>Manage your security preferences</p>
                    <div className="setting-item">
                        <div className="setting-info">
                            <span>Two-Factor Authentication</span>
                            <span className="setting-desc">Add an extra layer of security</span>
                        </div>
                        <button className="btn btn-secondary">Enable</button>
                    </div>
                    <div className="setting-item">
                        <div className="setting-info">
                            <span>Change Password</span>
                            <span className="setting-desc">Update your password</span>
                        </div>
                        <button className="btn btn-secondary">Change</button>
                    </div>
                </section>

                <section className="settings-section">
                    <h2><Globe size={20} />Language & Region</h2>
                    <p>Set your language and timezone preferences</p>
                    <div className="setting-item">
                        <div className="setting-info">
                            <span>Language</span>
                        </div>
                        <select className="select-input">
                            <option>English (US)</option>
                            <option>Spanish</option>
                            <option>French</option>
                        </select>
                    </div>
                    <div className="setting-item">
                        <div className="setting-info">
                            <span>Timezone</span>
                        </div>
                        <select className="select-input">
                            <option>UTC-5 (Eastern)</option>
                            <option>UTC-8 (Pacific)</option>
                            <option>UTC+0 (GMT)</option>
                        </select>
                    </div>
                </section>
            </div>
        </div>
    );
}

export default SettingsPage;
