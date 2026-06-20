import type { z } from "zod";
import type { TokenSchema } from "../schemas/token";

export type Token = z.infer<typeof TokenSchema>;
