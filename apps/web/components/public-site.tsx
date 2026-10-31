import {ArrowRight, Globe2} from "lucide-react";
import {getTranslations} from "next-intl/server";
import {Link} from "@/i18n/navigation";

export async function PublicHeader(){const t=await getTranslations();return <header className="public-header"><Link href="/catalog" className="public-brand"><span className="public-logo">Y</span><span><strong>Young Engineers</strong><small>Prishtina</small></span></Link><nav><Link href="/catalog">{t("catalog")}</Link><Link href="/faq">FAQ</Link><Link href="/contact">{t("contact")}</Link></nav><Link className="header-cta" href="/contact">{t("findProgram")} <ArrowRight size={16}/></Link></header>}

export async function PublicFooter(){const t=await getTranslations();return <footer className="public-footer"><div><div className="public-brand"><span className="public-logo">Y</span><span><strong>Young Engineers</strong><small>Prishtina</small></span></div><p>{t("publicTagline")}</p></div><div><strong>{t("explore")}</strong><Link href="/catalog">{t("catalog")}</Link><Link href="/faq">FAQ</Link><Link href="/contact">{t("contact")}</Link></div><div><strong>{t("languageLabel")}</strong><span><Globe2 size={15}/> Shqip · English</span></div></footer>}
