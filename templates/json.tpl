{% macro json(data) %}
    {% if data is string %}
        {{ data }}
    {% else %}
        {{ data|tojson|safe }}
    {% endif %}
{% endmacro %}
