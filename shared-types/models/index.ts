export enum UserRole {
  ADMIN = 'ADMIN',
  DEVELOPER = 'DEVELOPER',
  MANAGER = 'MANAGER',
}

export enum TaskStatus {
  TODO = 'TODO',
  IN_PROGRESS = 'IN_PROGRESS',
  REVIEW = 'REVIEW',
  DONE = 'DONE',
}

export enum TaskPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export interface User {
  id: string;
  email: string;
  fullName: string;
  avatarUrl?: string;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  ownerId: string;
  members: User[];
  createdAt: string;
  updatedAt: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  projectId: string;
  assigneeId?: string;
  tags: string[];
  dueDate?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  content: string;
  senderId: string;
  channelId?: string; // For group chat
  recipientId?: string; // For DM
  attachments?: string[];
  createdAt: string;
}

export interface WorkLog {
  id: string;
  userId: string;
  startTime: string;
  endTime?: string;
  activeWindow?: string;
  idleDurationSeconds: number;
  screenshotUrl?: string;
}
