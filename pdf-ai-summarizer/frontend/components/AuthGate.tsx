"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { getMe, login } from "@/lib/api";
import { clearToken, getToken, setToken } from "@/lib/auth";
import type { UserInfo } from "@/types/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthGateProps = {
  children: (user: UserInfo, onLogout: () => void) => ReactNode;
};

export function AuthGate({ children }: AuthGateProps) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<UserInfo | null>(null);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState("");

  async function checkExistingSession() {
    if (!getToken()) {
      setStatus("unauthenticated");
      return;
    }
    try {
      const me = await getMe();
      setUser(me);
      setStatus("authenticated");
    } catch {
      // Token cu het han/khong hop le - readErrorMessage trong lib/api.ts da
      // tu xoa token roi, chi can cap nhat lai UI.
      setStatus("unauthenticated");
    }
  }

  useEffect(() => {
    void checkExistingSession();

    // Bat su kien tu lib/api.ts - bat cu request nao khac trong app nhan 401
    // (vd token het han giua chung) deu bat quay lai man hinh dang nhap ngay,
    // khong can doi nguoi dung tu phat hien loi roi tu reload trang.
    function handleUnauthorized() {
      setUser(null);
      setStatus("unauthenticated");
    }
    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("auth:unauthorized", handleUnauthorized);
  }, []);

  async function handleLogin() {
    setLoggingIn(true);
    setLoginError("");
    try {
      const result = await login({ username, password });
      setToken(result.access_token);
      setUser(result.user);
      setStatus("authenticated");
      setUsername("");
      setPassword("");
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : "Dang nhap that bai");
    } finally {
      setLoggingIn(false);
    }
  }

  function handleLogout() {
    clearToken();
    setUser(null);
    setStatus("unauthenticated");
  }

  if (status === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6" />
      </main>
    );
  }

  if (status === "unauthenticated" || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4">
        <Card className="w-full max-w-sm">
          <h1 className="text-xl font-semibold">Đăng nhập</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            App này chỉ dành cho tài khoản đã được cấp trước.
          </p>

          <form
            className="mt-5 grid gap-4"
            onSubmit={(event) => {
              event.preventDefault();
              void handleLogin();
            }}
          >
            <label className="grid gap-2 text-sm font-medium">
              Tên đăng nhập
              <input
                autoFocus
                className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
                onChange={(event) => setUsername(event.target.value)}
                type="text"
                value={username}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              Mật khẩu
              <input
                className="min-h-10 rounded-lg border border-zinc-300 bg-zinc-50 px-3 text-sm outline-none focus:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-600"
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                value={password}
              />
            </label>

            {loginError ? <p className="text-sm text-red-600 dark:text-red-400">{loginError}</p> : null}

            <Button disabled={!username || !password} loading={loggingIn} type="submit">
              {loggingIn ? "Đang đăng nhập" : "Đăng nhập"}
            </Button>
          </form>
        </Card>
      </main>
    );
  }

  return <>{children(user, handleLogout)}</>;
}
