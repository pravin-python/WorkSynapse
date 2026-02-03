import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
// Icons
import { LayoutDashboard, MessageSquare, CheckSquare, Settings, Users } from 'lucide-react'

// Layout
const SidebarItem = ({ icon: Icon, label, active, onClick }: { icon: any, label: string, active?: boolean, onClick: () => void }) => (
    <div
        onClick={onClick}
        className={`
      flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all duration-200
      ${active ? 'bg-white/10 text-white' : 'text-gray-400 hover:text-white hover:bg-white/5'}
    `}
        style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer',
            backgroundColor: active ? 'hsl(var(--color-surface-active))' : 'transparent',
            color: active ? 'hsl(var(--color-primary))' : 'hsl(var(--color-text-muted))',
            borderLeft: active ? '3px solid hsl(var(--color-primary))' : '3px solid transparent'
        }}
    >
        <Icon size={20} />
        <span style={{ fontWeight: 500 }}>{label}</span>
    </div>
)

const Layout = ({ children }: { children: React.ReactNode }) => {
    const [activeTab, setActiveTab] = useState('dashboard')

    return (
        <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
            {/* Sidebar */}
            <div className="glass-panel" style={{
                width: '260px',
                height: '100%',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '2rem',
                zIndex: 10
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', background: 'hsl(var(--color-primary))', borderRadius: '8px' }}></div>
                    <h2 className="gradient-text" style={{ fontSize: '1.25rem', margin: 0 }}>WorkSynapse</h2>
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <SidebarItem icon={LayoutDashboard} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
                    <SidebarItem icon={MessageSquare} label="Chat" active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
                    <SidebarItem icon={CheckSquare} label="Tasks" active={activeTab === 'tasks'} onClick={() => setActiveTab('tasks')} />
                    <SidebarItem icon={Users} label="Team" active={activeTab === 'team'} onClick={() => setActiveTab('team')} />
                    <div style={{ flex: 1 }}></div>
                    <SidebarItem icon={Settings} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
                </nav>
            </div>

            {/* Main Content */}
            <main style={{ flex: 1, overflowY: 'auto', padding: '2rem', position: 'relative' }}>
                {/* Background decorations */}
                <div style={{
                    position: 'fixed',
                    top: '-20%',
                    right: '-10%',
                    width: '50vw',
                    height: '50vw',
                    background: 'radial-gradient(circle, hsl(var(--color-primary) / 0.15) 0%, transparent 70%)',
                    filter: 'blur(100px)',
                    zIndex: -1,
                    pointerEvents: 'none'
                }}></div>

                {children}
            </main>
        </div>
    )
}

function App() {
    return (
        <Router>
            <Layout>
                <Routes>
                    <Route path="/" element={
                        <div>
                            <header style={{ marginBottom: '2rem' }}>
                                <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Good Morning, Alex</h1>
                                <p style={{ color: 'hsl(var(--color-text-muted))' }}>Here's what's happening in your workspace today.</p>
                            </header>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                                {/* Stats Card */}
                                <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: 'var(--radius-lg)' }}>
                                    <h3 style={{ color: 'hsl(var(--color-text-muted))', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Active Tasks</h3>
                                    <div style={{ fontSize: '2.5rem', fontWeight: 700 }}>12</div>
                                    <div style={{ color: 'hsl(140 60% 50%)', fontSize: '0.875rem', marginTop: '0.5rem' }}>+2 from yesterday</div>
                                </div>

                                <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: 'var(--radius-lg)' }}>
                                    <h3 style={{ color: 'hsl(var(--color-text-muted))', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Team Velocity</h3>
                                    <div style={{ fontSize: '2.5rem', fontWeight: 700 }}>84%</div>
                                    <div style={{ color: 'hsl(var(--color-primary))', fontSize: '0.875rem', marginTop: '0.5rem' }}>On track</div>
                                </div>

                                <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: 'var(--radius-lg)' }}>
                                    <h3 style={{ color: 'hsl(var(--color-text-muted))', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Unread Messages</h3>
                                    <div style={{ fontSize: '2.5rem', fontWeight: 700 }}>5</div>
                                    <div style={{ color: 'hsl(var(--color-text-muted))', fontSize: '0.875rem', marginTop: '0.5rem' }}>Check Team Chat</div>
                                </div>
                            </div>

                        </div>
                    } />
                </Routes>
            </Layout>
        </Router>
    )
}

export default App
