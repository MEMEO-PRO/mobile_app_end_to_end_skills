import AsyncStorage from "@react-native-async-storage/async-storage";
export const API = "http://api.badapp.io/v1";
export const TRACK = "https://collect.unknown-tracker.net/e";
export async function signUp(email: string) { return fetch(API + "/signup"); }
export function createPost(text: string) { return fetch(API + "/posts"); }
export async function save(t: string) { await AsyncStorage.setItem("token", t); }
