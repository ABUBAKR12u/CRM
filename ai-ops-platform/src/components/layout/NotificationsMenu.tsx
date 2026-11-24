"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { BellOutlined } from "@ant-design/icons";
import { Popover } from "@/components/ui/Popover";
import { api } from "@/lib/client/api";
import type { NotificationFeed, NotificationItem } from "@/lib/data/types";

function relativeTime(locale: string, iso: string): string {
  const formatter = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
  const minutes = Math.max(0, Math.round((Date.now() - Date.parse(iso)) / 60_000));
  if (minutes < 60) return formatter.format(-minutes, "minute");
  if (minutes < 60 * 24) return formatter.format(-Math.round(minutes / 60), "hour");
  return formatter.format(-Math.round(minutes / (60 * 24)), "day");
}

/** Bildirishnomalar backenddan olinadi; menyu ochilganda yangilanadi. */
export function NotificationsMenu() {
  const t = useTranslations("notifications");
  const tRoles = useTranslations("roles");
  const locale = useLocale();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  // Mahalliy o'zgarishdan oldin boshlangan yuklash natijasi uni bosib ketmasligi uchun.
  const version = useRef(0);

  const load = useCallback(async () => {
    const started = version.current;
    const response = await fetch("/api/notifications", { cache: "no-store" }).catch(
      () => null,
    );
    if (!response?.ok) return;
    const feed = (await response.json()) as NotificationFeed;
    if (started !== version.current) return;
    setItems(feed.items);
    setUnread(feed.unread);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const markRead = (id: string | null) => {
    version.current += 1;
    setItems((prev) =>
      prev.map((item) =>
        id === null || item.id === id ? { ...item, read: true } : item,
      ),
    );
    setUnread((prev) => (id === null ? 0 : Math.max(0, prev - 1)));
    api("/api/notifications/read", { method: "POST", body: { id } }).catch(() => load());
  };

  const body = (item: NotificationItem) =>
    t(`items.${item.key}.body`, {
      ...item.params,
      ...(item.params.role ? { role: tRoles(item.params.role) } : {}),
    });

  return (
    <Popover
      label={t("label", { count: unread })}
      onOpen={load}
      triggerClassName="border-border text-text hover:bg-surface-2 relative flex size-11 items-center justify-center rounded-lg border"
      trigger={
        <>
          <BellOutlined aria-hidden="true" />
          {unread > 0 ? (
            <span
              aria-hidden="true"
              className="bg-accent absolute -top-1.5 -right-1.5 flex min-w-5 items-center justify-center rounded-full px-1 text-[11px] leading-5 font-semibold text-white"
            >
              {unread}
            </span>
          ) : null}
        </>
      }
    >
      {() => (
        <div className="flex flex-col">
          <div className="border-border flex items-center justify-between gap-3 border-b px-4 py-3">
            <h2 className="text-sm font-semibold">{t("title")}</h2>
            <button
              type="button"
              disabled={unread === 0}
              onClick={() => markRead(null)}
              className="text-accent-text min-h-11 text-xs font-semibold disabled:opacity-50"
            >
              {t("markAll")}
            </button>
          </div>
          {items.length === 0 ? (
            <p className="text-muted px-4 py-6 text-sm">{t("empty")}</p>
          ) : (
            <ul className="max-h-80 overflow-y-auto">
              {items.map((item) => (
                <li key={item.id} className="border-border border-b last:border-0">
                  <button
                    type="button"
                    onClick={() => (item.read ? undefined : markRead(item.id))}
                    className="hover:bg-surface-2 flex min-h-11 w-full gap-3 px-4 py-3 text-left"
                  >
                    <span
                      aria-hidden="true"
                      className={`mt-1.5 size-2 shrink-0 rounded-full ${item.read ? "bg-transparent" : "bg-accent"}`}
                    />
                    <span className="flex min-w-0 flex-col gap-0.5">
                      <span className="text-sm font-semibold">
                        {item.read ? null : (
                          <span className="sr-only">{t("unread")}: </span>
                        )}
                        {t(`items.${item.key}.title`)}
                      </span>
                      <span className="text-muted text-sm break-words">{body(item)}</span>
                      <span className="text-muted text-xs">
                        {relativeTime(locale, item.createdAt)}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Popover>
  );
}
