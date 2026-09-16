export type Role = 'admin' | 'user';
export type Status = 'idea' | 'drafting' | 'review' | 'approved' | 'rendering' | 'ready' | 'posted';
export interface TeamUser { id: string; name: string; email: string; role: Role; active: boolean; }
export interface Brand { id: string; name: string; tagline?: string; site?: string; logoUrl?: string; colors: { primary: string; accent: string; ink: string; paper: string }; voice: { provider: 'qwen'; profileName: string; model: string; instructions: string; pronunciationNotes?: string }; }
export interface VideoPackage { id: string; brandId: string; headline: string; status: Status; imageUrl?: string; script?: string; assignedTo?: string; updatedAt?: string; }
