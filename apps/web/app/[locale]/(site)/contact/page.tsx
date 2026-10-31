import {Mail,MapPin,MessageCircle} from "lucide-react";
import {getTranslations} from "next-intl/server";
import {InquiryForm} from "@/components/inquiry-form";
export default async function ContactPage(){const t=await getTranslations();return <section className="contact-layout"><div><span className="public-kicker"><MessageCircle size={15}/>{t("talkToUs")}</span><h1>{t("contactTitle")}</h1><p>{t("contactIntro")}</p><div className="contact-points"><span><MapPin/>Prishtina, Kosovë</span><span><Mail/>info@yeprishtina.com</span></div></div><div className="contact-card"><InquiryForm/></div></section>}
