CREATE TABLE "public"."pereval_areas" (
    "id" int8 NOT NULL DEFAULT nextval('pereval_areas_id_seq'::regclass),
    "id_parent" int8 NOT NULL,
    "title" text NOT NULL,
    PRIMARY KEY ("id"),
    UNIQUE ("title"),  -- Уникальность заголовка
    FOREIGN KEY ("id_parent") REFERENCES "public"."pereval_areas"("id") ON DELETE CASCADE  -- Внешний ключ
);

CREATE INDEX idx_pereval_areas_id_parent ON "public"."pereval_areas" ("id_parent");
