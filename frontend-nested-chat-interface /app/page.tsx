"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export default function LoginPage() {
  const [authModalOpen, setAuthModalOpen] = useState(true)
  const [isLoginMode, setIsLoginMode] = useState(true)
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState("")
  const [userEmail, setUserEmail] = useState("")
  const [userPassword, setUserPassword] = useState("")
  const router = useRouter()

  // Handle login/register
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthLoading(true)
    setAuthError("")
    try {
      if (isLoginMode) {
        // LOGIN: /auth/token, form data, username/password
        const formData = new FormData();
        formData.append("username", userEmail);
        formData.append("password", userPassword);
        const res = await fetch("http://localhost:8000/auth/token", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (!res.ok || !data.access_token) throw new Error(data.detail || "Auth failed");
        localStorage.setItem("jwt", data.access_token);
        setAuthModalOpen(false);
        router.push("/chat");
      } else {
        // REGISTER: /auth/register, JSON, username/password
        const res = await fetch("http://localhost:8000/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: userEmail, password: userPassword }),
        });
        const data = await res.json();
        if (!res.ok || !data.id) throw new Error(data.detail || "Registration failed");
        // Optionally auto-login after register
        setIsLoginMode(true);
        setAuthError("Registration successful! Please log in.");
      }
    } catch (err: any) {
      setAuthError(err.message || "Auth error");
    } finally {
      setAuthLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Dialog open={authModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{isLoginMode ? "Login" : "Register"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAuth} className="space-y-4">
            <Input
              type="email"
              placeholder="Email"
              value={userEmail}
              onChange={e => setUserEmail(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="Password"
              value={userPassword}
              onChange={e => setUserPassword(e.target.value)}
              required
            />
            {authError && <div className="text-red-500 text-sm">{authError}</div>}
            <Button type="submit" className="w-full" disabled={authLoading}>
              {authLoading ? "Loading..." : isLoginMode ? "Login" : "Register"}
            </Button>
            <div className="text-center text-sm mt-2">
              {isLoginMode ? (
                <>
                  Don't have an account?{' '}
                  <button type="button" className="text-blue-600 underline" onClick={() => setIsLoginMode(false)}>
                    Register
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{' '}
                  <button type="button" className="text-blue-600 underline" onClick={() => setIsLoginMode(true)}>
                    Login
                  </button>
                </>
              )}
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
