import * as SecureStore from "expo-secure-store";
export const API = "https://abcd.supabase.co/rest/v1";
export async function signUp(email: string) { return fetch(API + "/signup"); }
export async function deleteAccount() { return fetch(API + "/account", { method: "DELETE" }); }
export async function restorePurchases() { /* RevenueCat restore */ }
export async function saveToken(t: string) { await SecureStore.setItemAsync("token", t); }
