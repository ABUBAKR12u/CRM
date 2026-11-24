import { getTranslations, setRequestLocale } from "next-intl/server";
import { PageHeader } from "@/components/layout/PageHeader";
import { TasksView } from "@/components/tasks/TasksView";
import { requirePageActor } from "@/lib/auth/actor-page";
import { assignablePeople, listTasks, orThrow, todayIso } from "@/lib/data/service";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "nav" });
  return { title: t("tasks") };
}

export default async function TasksPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const actor = await requirePageActor(locale, "tasks");
  const t = await getTranslations("tasks");
  const [tasks, assignees] = await Promise.all([
    listTasks(actor),
    assignablePeople(actor),
  ]);

  return (
    <>
      <PageHeader title={t("title")} subtitle={t(`subtitle.${actor.role}`)} />
      <TasksView
        tasks={orThrow(tasks)}
        assignees={orThrow(assignees)}
        role={actor.role}
        today={todayIso()}
      />
    </>
  );
}
