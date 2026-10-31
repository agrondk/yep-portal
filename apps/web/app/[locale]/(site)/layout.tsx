import {PublicFooter,PublicHeader} from "@/components/public-site";
export default function SiteLayout({children}:{children:React.ReactNode}){return <div className="public-site"><PublicHeader/><main>{children}</main><PublicFooter/></div>}
