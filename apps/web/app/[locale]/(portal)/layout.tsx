import {cookies} from "next/headers";
import {redirect} from "next/navigation";
import {PortalShell} from "@/components/portal-shell";
export default async function Layout({children,params}:{children:React.ReactNode;params:Promise<{locale:string}>}){const {locale}=await params;const session=(await cookies()).get("yep_session");if(!session)redirect(`/${locale}/login`);return <PortalShell>{children}</PortalShell>}
