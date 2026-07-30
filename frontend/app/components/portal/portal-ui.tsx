"use client";

import {
  ArrowRight,
  Bell,
  ChevronDown,
  Inbox,
  LoaderCircle,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  Search,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import {
  apiRequest,
  type LiveNotification,
  type PaginatedResponse,
  type WorkspaceSession,
  unpackList,
} from "../../lib/api";
import { RbisBrand } from "../rbis-brand";

export type NavItem = { id: string; label: string; icon: LucideIcon; badge?: string };

export function WorkspaceShell({
  session,
  nav,
  active,
  onChange,
  onLogout,
  roleLabel,
  children,
}: {
  session: WorkspaceSession;
  nav: NavItem[];
  active: string;
  onChange: (id: string) => void;
  onLogout: () => void;
  roleLabel: string;
  children: ReactNode;
}) {
  const initials = session.user.full_name.split(" ").map((part) => part[0]).slice(0, 2).join("");
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    if (typeof window === "undefined") return true;
    return window.localStorage.getItem("bilimyol_sidebar_open") !== "false";
  });
  const [notifications, setNotifications] = useState<LiveNotification[]>([]);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notificationsLoading, setNotificationsLoading] = useState(true);
  const [notificationsError, setNotificationsError] = useState("");

  const unreadCount = useMemo(
    () => notifications.filter((item) => !item.is_read).length,
    [notifications],
  );

  const loadNotifications = async () => {
    setNotificationsLoading(true);
    setNotificationsError("");
    try {
      const payload = await apiRequest<PaginatedResponse<LiveNotification> | LiveNotification[]>(
        "/notifications/?page_size=20&ordering=-created_at",
      );
      setNotifications(unpackList(payload));
    } catch (error) {
      setNotificationsError(error instanceof Error ? error.message : "Bildirishnomalar yuklanmadi.");
    } finally {
      setNotificationsLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => void loadNotifications(), 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const closeSidebarForExam = () => {
      setSidebarOpen(false);
      window.localStorage.setItem("bilimyol_sidebar_open", "false");
    };
    window.addEventListener("bilimyol-exam-start", closeSidebarForExam);
    return () => window.removeEventListener("bilimyol-exam-start", closeSidebarForExam);
  }, []);

  const toggleSidebar = () => {
    setSidebarOpen((current) => {
      const next = !current;
      window.localStorage.setItem("bilimyol_sidebar_open", String(next));
      return next;
    });
  };

  const openNotification = async (notification: LiveNotification) => {
    if (!notification.is_read) {
      try {
        const updated = await apiRequest<LiveNotification>(
          `/notifications/${notification.id}/mark-read/`,
          { method: "POST" },
        );
        setNotifications((current) => current.map((item) => item.id === updated.id ? updated : item));
      } catch {
        // Navigation remains available even when marking read fails.
      }
    }
    if (notification.action_path && nav.some((item) => item.id === notification.action_path)) {
      onChange(notification.action_path);
      setNotificationsOpen(false);
    }
  };

  const markAllRead = async () => {
    try {
      await apiRequest("/notifications/mark-all-read/", { method: "POST" });
      setNotifications((current) => current.map((item) => ({ ...item, is_read: true })));
    } catch (error) {
      setNotificationsError(error instanceof Error ? error.message : "Bildirishnomalar yangilanmadi.");
    }
  };

  return (
    <main className={`workspace-shell ${sidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
      <aside className="workspace-sidebar" aria-hidden={!sidebarOpen}>
        <RbisBrand inverse className="portal-brand" />
        <div className="workspace-role"><span>{roleLabel}</span><small>RBIS · BilimYo‘l</small></div>
        <nav aria-label={`${roleLabel} bo‘limlari`}>
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.id} className={active === item.id ? "active" : ""} onClick={() => onChange(item.id)}>
                <Icon size={18} /><span>{item.label}</span>{item.badge && <em>{item.badge}</em>}
              </button>
            );
          })}
        </nav>
        <div className="sidebar-support"><Sparkles size={18} /><strong>Yordam kerakmi?</strong><p>Metodist bilan 0000 raqami orqali bog‘laning.</p><a href="tel:0000">Yordam markazi <ArrowRight size={14} /></a></div>
        <button className="sidebar-logout" onClick={onLogout}><LogOut size={17} /> Tizimdan chiqish</button>
      </aside>

      <section className="workspace-main">
        <header className="workspace-topbar">
          <div className="topbar-left">
            <button className="sidebar-toggle" onClick={toggleSidebar} aria-label={sidebarOpen ? "Yon menyuni yopish" : "Yon menyuni ochish"} aria-expanded={sidebarOpen}>
              {sidebarOpen ? <PanelLeftClose size={19} /> : <PanelLeftOpen size={19} />}
            </button>
            <div className="workspace-search"><Search size={17} /><input aria-label="Kabinet bo‘yicha izlash" placeholder="Qidirish..." /></div>
          </div>
          <div className="topbar-actions">
            <div className="notification-center">
              <button aria-label="Bildirishnomalar" onClick={() => setNotificationsOpen((current) => !current)}>
                <Bell size={18} />{unreadCount > 0 && <i />}
              </button>
              {notificationsOpen && (
                <aside className="notification-panel">
                  <div className="notification-panel-head">
                    <div><strong>Bildirishnomalar</strong><small>{unreadCount} ta o‘qilmagan</small></div>
                    {unreadCount > 0 && <button type="button" onClick={() => void markAllRead()}>Barchasini o‘qish</button>}
                  </div>
                  {notificationsLoading ? (
                    <div className="notification-state"><LoaderCircle className="spin" size={21} /> Yuklanmoqda...</div>
                  ) : notificationsError ? (
                    <div className="notification-state error"><span>{notificationsError}</span><button onClick={() => void loadNotifications()}><RefreshCw size={15} /></button></div>
                  ) : notifications.length ? (
                    <div className="notification-list">
                      {notifications.map((item) => (
                        <button type="button" className={item.is_read ? "" : "unread"} key={item.id} onClick={() => void openNotification(item)}>
                          <span /><div><strong>{item.title}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString("uz-UZ")}</small></div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="notification-state"><Inbox size={22} /> Bildirishnoma yo‘q</div>
                  )}
                </aside>
              )}
            </div>
            <div className="profile-chip"><span>{initials}</span><div><strong>{session.user.full_name}</strong><small>{roleLabel}</small></div><ChevronDown size={15} /></div>
          </div>
        </header>
        <div className="workspace-content">{children}</div>
      </section>
    </main>
  );
}

export function MetricCard({ icon: Icon, label, value, note, tone = "navy" }: { icon: LucideIcon; label: string; value: string | number; note: string; tone?: string }) {
  return <article className={`portal-metric ${tone}`}><span><Icon size={20} /></span><div><small>{label}</small><strong>{value}</strong><p>{note}</p></div></article>;
}

export function ScoreRing({ score, label }: { score: number; label: string }) {
  return <div className="mini-score-ring" style={{ "--score": `${score * 3.6}deg` } as CSSProperties}><div><strong>{score}</strong><small>/100</small></div><span>{label}</span></div>;
}

export function SubjectProgress({ title, score, color }: { title: string; score: number; color: string }) {
  const normalized = Math.max(0, Math.min(100, Math.round(score)));
  return <div className="subject-progress"><div><strong>{title}</strong><span>{normalized}/100</span></div><div><i style={{ width: `${normalized}%`, background: color }} /></div></div>;
}

export function PageTitle({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <div className="portal-page-title"><div><span>{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}

export function LoadingState({ label = "Ma’lumotlar yuklanmoqda..." }: { label?: string }) {
  return <article className="portal-card portal-data-state"><LoaderCircle className="spin" size={28} /><h2>{label}</h2></article>;
}

export function EmptyState({ title, description, icon: Icon = Inbox }: { title: string; description: string; icon?: LucideIcon }) {
  return <article className="portal-card portal-data-state"><Icon size={30} /><h2>{title}</h2><p>{description}</p></article>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <article className="portal-card portal-data-state error"><RefreshCw size={27} /><h2>Ma’lumotni olib bo‘lmadi</h2><p>{message}</p>{onRetry && <button className="portal-secondary" onClick={onRetry}><RefreshCw size={15} /> Qayta urinish</button>}</article>;
}
