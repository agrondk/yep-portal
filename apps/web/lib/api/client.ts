import createClient from "openapi-fetch";
import type {paths} from "./schema";
export const API_URL=process.env.NEXT_PUBLIC_API_URL??"http://127.0.0.1:8000/api/v1";
export const api=createClient<paths>({baseUrl:API_URL,credentials:"include"});
