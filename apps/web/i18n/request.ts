import {getRequestConfig} from "next-intl/server";
import {hasLocale} from "next-intl";
import {routing} from "./routing";
export default getRequestConfig(async ({requestLocale})=>{const requested=await requestLocale;const locale=hasLocale(routing.locales,requested)?requested:routing.defaultLocale;const core=(await import(`../messages/${locale}/core.json`)).default;const catalog=(await import(`../messages/${locale}/catalog.json`)).default;const editor=(await import(`../messages/${locale}/editor.json`)).default;return {locale,messages:{...core,...catalog,...editor}};});
