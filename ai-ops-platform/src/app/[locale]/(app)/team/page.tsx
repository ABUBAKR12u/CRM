import { getTranslations, setRequestLocale } from "next-intl/server";
import { PageHeader } from "@/components/layout/PageHeader";
import { TeamView } from "@/components/team/TeamView";
import { requirePageActor } from "@/lib/auth/actor-page";
import { orThrow, teamRows, todayIso } from "@/lib/data/service";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "nav" });
  return { title: t("team") };
}

export default async function TeamPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const actor = await requirePageActor(locale, "team");
  const t = await getTranslations("team");
  const rows = orThrow(await teamRows(actor));

  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <TeamView
        rows={rows}
        assignees={rows.map(({ id, name }) => ({ id, name }))}
        today={todayIso()}
      />
    </>
  );
}
