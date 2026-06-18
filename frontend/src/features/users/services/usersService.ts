import type { WithAuthenticatedRequest } from "../../../types";

import type { User } from "../types";
import { getUsers } from "./userApi";


export async function fetchUsers(withAuthenticatedRequest: WithAuthenticatedRequest): Promise<User[]> {
  debugger;
  return withAuthenticatedRequest((token) => getUsers(token));
}

