{% macro ric_sql_literal(value) -%}
    {%- if value is none -%}
        NULL
    {%- else -%}
        '{{ (value | string).replace("'", "''") }}'
    {%- endif -%}
{%- endmacro %}

{% macro persist_dbt_results(results) %}
    {% if execute and flags.WHICH in ['build', 'test', 'run', 'seed', 'snapshot'] and results %}
        CREATE TABLE IF NOT EXISTS ops.dbt_run_results (
            invocation_id TEXT NOT NULL,
            unique_id TEXT NOT NULL,
            run_started_at TIMESTAMPTZ NOT NULL,
            recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            command TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            node_name TEXT NOT NULL,
            model_name TEXT,
            column_name TEXT,
            status TEXT NOT NULL,
            severity TEXT,
            failures BIGINT,
            execution_time DOUBLE PRECISION,
            message TEXT,
            PRIMARY KEY (invocation_id, unique_id)
        );
        CREATE INDEX IF NOT EXISTS dbt_run_results_started_idx
            ON ops.dbt_run_results (run_started_at DESC);
        CREATE TABLE IF NOT EXISTS ops.dbt_test_failures (
            invocation_id TEXT NOT NULL,
            unique_id TEXT NOT NULL,
            row_number BIGINT NOT NULL,
            row_data JSONB NOT NULL,
            PRIMARY KEY (invocation_id, unique_id, row_number),
            FOREIGN KEY (invocation_id, unique_id)
                REFERENCES ops.dbt_run_results (invocation_id, unique_id)
                ON DELETE CASCADE
        );

        {% for result in results if result.node.resource_type in ['test', 'model', 'seed', 'snapshot'] %}
            {% set node = result.node %}
            {% set status = result.status.value if result.status.value is defined else result.status %}
            {% set parents = [] %}
            {% for parent_id in node.depends_on.nodes %}
                {% if parent_id in graph.nodes and graph.nodes[parent_id].resource_type == 'model' %}
                    {% do parents.append(graph.nodes[parent_id].name) %}
                {% endif %}
            {% endfor %}
            INSERT INTO ops.dbt_run_results (
                invocation_id, unique_id, run_started_at, command, resource_type,
                node_name, model_name, column_name, status, severity, failures,
                execution_time, message
            ) VALUES (
                {{ ric_sql_literal(invocation_id) }},
                {{ ric_sql_literal(node.unique_id) }},
                {{ ric_sql_literal(run_started_at.isoformat()) }}::TIMESTAMPTZ,
                {{ ric_sql_literal(flags.WHICH) }},
                {{ ric_sql_literal(node.resource_type) }},
                {{ ric_sql_literal(node.name) }},
                {{ ric_sql_literal(parents | join(', ') if node.resource_type == 'test' else node.name) }},
                {{ ric_sql_literal(node.column_name if node.column_name is defined else none) }},
                {{ ric_sql_literal(status) }},
                {{ ric_sql_literal(node.config.severity | lower if node.resource_type == 'test' else none) }},
                {{ result.failures if result.failures is not none else 'NULL' }},
                {{ result.execution_time }},
                {{ ric_sql_literal(result.message) }}
            ) ON CONFLICT (invocation_id, unique_id) DO UPDATE SET
                recorded_at = CURRENT_TIMESTAMP,
                status = EXCLUDED.status,
                failures = EXCLUDED.failures,
                execution_time = EXCLUDED.execution_time,
                message = EXCLUDED.message;

            DELETE FROM ops.dbt_test_failures
            WHERE invocation_id = {{ ric_sql_literal(invocation_id) }}
              AND unique_id = {{ ric_sql_literal(node.unique_id) }};

            {% if node.resource_type == 'test' and node.config.store_failures and status in ['warn', 'fail'] %}
                INSERT INTO ops.dbt_test_failures (
                    invocation_id, unique_id, row_number, row_data
                )
                SELECT
                    {{ ric_sql_literal(invocation_id) }},
                    {{ ric_sql_literal(node.unique_id) }},
                    ROW_NUMBER() OVER (),
                    TO_JSONB(failure)
                FROM {{ adapter.quote(node.schema) }}.{{ adapter.quote(node.alias) }} AS failure;
            {% endif %}
        {% endfor %}

        CREATE OR REPLACE VIEW ops.v_dbt_latest_results AS
        SELECT DISTINCT ON (unique_id) *
        FROM ops.dbt_run_results
        ORDER BY unique_id, run_started_at DESC, recorded_at DESC;

        GRANT SELECT ON ops.dbt_run_results, ops.dbt_test_failures,
            ops.v_dbt_latest_results TO metabase_ops_user;
    {% endif %}
{% endmacro %}
