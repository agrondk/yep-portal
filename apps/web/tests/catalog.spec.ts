import {expect,test} from "@playwright/test";

test("published offering appears while draft stays hidden",async({page})=>{
  await page.route("**/public/offerings?*",async route=>route.fulfill({json:[{
    id:"11111111-1111-1111-1111-111111111111",slug:"bricks-confirmed",program_id:"22222222-2222-2222-2222-222222222222",location_id:"33333333-3333-3333-3333-333333333333",partner_id:null,title_sq:null,title_en:null,program_slug:"bricks-challenge",program_name_sq:"Bricks Challenge i konfirmuar",program_name_en:"Confirmed Bricks Challenge",program_category:"course",description_sq:"Ndërto mekanizma dhe zgjidh probleme.",description_en:"Build mechanisms and solve problems.",learning_objectives_sq:null,learning_objectives_en:null,language:"sq",age_min:7,age_max:10,age_reference_date:"2026-09-01",start_date:"2026-09-01",end_date:"2026-12-15",session_minutes:75,sessions_planned:14,capacity:16,fee_model:"per_child_term",list_price:"120.00",currency:"EUR",visibility:"published",registration_open:true,waitlist_enabled:false
  }]}));
  await page.goto("/sq/catalog");
  await expect(page.getByText("Bricks Challenge i konfirmuar")).toBeVisible();
  await expect(page.getByText("Program draft i fshehur")).toHaveCount(0);
});
