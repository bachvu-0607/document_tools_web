export type LoginRequest = {
  username: string;
  password: string;
};

export type UserInfo = {
  id: string;
  username: string;
  display_name: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: UserInfo;
};
