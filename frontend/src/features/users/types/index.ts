export interface User {
  id: number;
  username: string;
}

export interface UpdateProfileInput {
  name: string;
  avatarUrl?: string;
}
