import {Sparkles} from "lucide-react";
import {getTranslations} from "next-intl/server";
import {CatalogBrowser} from "@/components/catalog-browser";
export default async function CatalogPage(){const t=await getTranslations();return <><section className="catalog-hero"><span className="public-kicker"><Sparkles size={15}/>{t("learningForBuilders")}</span><h1>{t("catalogTitle")}</h1><p>{t("catalogIntro")}</p></section><section className="catalog-section"><CatalogBrowser/></section></>}
