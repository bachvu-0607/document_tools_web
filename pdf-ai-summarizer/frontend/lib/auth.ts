const TOKEN_KEY = "pdf_ai_summarizer_token";

// localStorage chi ton tai trong trinh duyet - phai kiem tra "typeof window"
// vi Next.js co the chay code nay o phia server (khong co window) luc render.
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

// Header dinh kem vao moi request goi API can dang nhap - JWT khong tu dong
// gui kem nhu cookie, phai chu dong gan tay o day (xem giai thich JWT vs cookie).
export function authHeader(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
