resource "aws_glue_catalog_database" "qs_blog_db" {
  name = "${var.prefix}-db"
  tags = var.default_tags
}
resource "aws_glue_catalog_table" "qs_analysis_details" {
  name          = "${var.prefix}-analysis-details"
  database_name = aws_glue_catalog_database.qs_blog_db.name
  table_type    = "EXTERNAL_TABLE"
  parameters = {
    EXTERNAL                = "TRUE"
    "ignore.malformed.json" = "true"
  }
  storage_descriptor {
    location      = "s3://${module.column_extractor_results_bucket.s3_bucket_id}/analyses"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat"
    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "serialization.format" = 1
      }
    }
    columns {
      name    = "name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "datasetname"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "datasetid"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "columnname"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "calculatedcolumnname"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "usedcolumns"
      type    = "array<string>"
      comment = "from deserializer"
    }
  }
}
resource "aws_glue_catalog_table" "qs_dashboard_details" {
  name          = "${var.prefix}-dashboard-details"
  database_name = aws_glue_catalog_database.qs_blog_db.name
  table_type    = "EXTERNAL_TABLE"
  parameters = {
    EXTERNAL                = "TRUE"
    "ignore.malformed.json" = "true"
  }
  storage_descriptor {
    location      = "s3://${module.column_extractor_results_bucket.s3_bucket_id}/dashboards"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat"
    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "serialization.format" = 1
      }
    }
    columns {
      name    = "name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "datasetname"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "datasetid"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "columnname"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "calculatedcolumnname"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "usedcolumns"
      type    = "array<string>"
      comment = "from deserializer"
    }
  }
}
resource "aws_glue_catalog_table" "qs_dataset_details" {
  name          = "${var.prefix}-dataset-details"
  database_name = aws_glue_catalog_database.qs_blog_db.name
  table_type    = "EXTERNAL_TABLE"
  parameters = {
    EXTERNAL                = "TRUE"
    "ignore.malformed.json" = "true"
  }
  storage_descriptor {
    location      = "s3://${module.column_extractor_results_bucket.s3_bucket_id}/datasets"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat"
    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "serialization.format" = 1
      }
    }
    columns {
      name    = "datasetid"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "datasetname"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "rlsdatasetid"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "columnname"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "columntype"
      type    = "string"
      comment = "from deserializer"
    }
  }
}
resource "aws_athena_named_query" "qs_column_level_lineage_view" {
  name      = "${var.prefix}-column-level-lineage-view"
  database  = aws_glue_catalog_database.qs_blog_db.name
  query     = <<-EOF
                create or replace view "qs_column_level_lineage_view" as
                with
                map_table as (
                    select distinct
                    name,
                    b.datasetname as new_name,
                    a.datasetname as old_name
                    from
                    qs_analysis_details a
                    inner join qs_dataset_details b on (a.datasetid = b.datasetid)
                    where (a.datasetname <> b.datasetname)
                ),
                map_table_2 as (
                    select distinct
                    name,
                    b.datasetname as new_name,
                    a.datasetname as old_name
                    from
                    qs_dashboard_details a
                    inner join qs_dataset_details b on (a.datasetid = b.datasetid)
                    where (a.datasetname <> b.datasetname)
                ),
                lv1_analysis_details as (
                    select
                    a.name,
                    coalesce(b.new_name, a.datasetname) as datasetname,
                    coalesce(columnname, usedcolumnname) as columnname
                    from
                    qs_analysis_details a
                    left join map_table b on ((a.name = b.name) and (b.old_name = a.datasetname)),
                    unnest(usedcolumns) t (usedcolumnname)
                    union
                    select
                    a.name,
                    coalesce(b.new_name, a.datasetname) as datasetname,
                    columnname
                    from
                    qs_analysis_details a
                    left join map_table b on ((a.name = b.name) and (b.old_name = a.datasetname))
                    where (columnname is not null)
                ),
                lv2_dashboard_details as (
                    select
                    a.name,
                    coalesce(b.new_name, a.datasetname) as datasetname,
                    coalesce(columnname, usedcolumnname) as columnname
                    from
                    qs_dashboard_details a
                    left join map_table_2 b on ((a.name = b.name) and (b.old_name = a.datasetname)),
                    unnest(usedcolumns) t (usedcolumnname)
                    union
                    select
                    a.name,
                    coalesce(b.new_name, a.datasetname) as datasetname,
                    columnname
                    from
                    qs_dashboard_details a
                    left join map_table_2 b on ((a.name = b.name) and (b.old_name = a.datasetname))
                    where (columnname is not null)
                ),
                unique_analysis_details as (
                    select distinct
                    datasetname,
                    columnname,
                    name
                    from
                    lv1_analysis_details
                ),
                unique_dashboard_details as (
                    select distinct
                    datasetname,
                    columnname,
                    name
                    from
                    lv2_dashboard_details
                )
                select
                    a.datasetname,
                    a.columnname,
                    a.columntype,
                    (select listagg(name, ', ' on overflow error) within group (order by name asc)
                    from
                        unique_analysis_details uad
                    where ((uad.datasetname = a.datasetname) and (uad.columnname = a.columnname))
                    ) as analysis_usage,
                    (select listagg(name, ', ' on overflow error) within group (order by name asc)
                    from
                        unique_dashboard_details udd
                    where ((udd.datasetname = a.datasetname) and (udd.columnname = a.columnname))
                    ) as dashboard_usage,
                    max((case when (b.name is null) then 0 else 1 end)) as used_in_analysis,
                    max((case when (c.name is null) then 0 else 1 end)) as used_in_dashboard,
                    max((case when (exists (select 1
                    from
                        qs_dataset_details
                    where ((a.rlsdatasetid = datasetid) and (columnname = a.columnname))
                    )) then 1 else 0 end)) as used_in_rls_dataset
                from
                    qs_dataset_details a
                    left join lv1_analysis_details b on ((a.datasetname = b.datasetname) and (a.columnname = b.columnname))
                    left join lv2_dashboard_details c on ((a.datasetname = c.datasetname) and (a.columnname = c.columnname))
                group by 1, 2, 3
            EOF
  workgroup = "primary"
}
