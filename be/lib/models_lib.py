from lib.util import getattr_with_lookup_key


def group_queryset_by_field(queryset, fieldname):
    """Group a queryset by a fieldname, yielding lists of instances with the same value for that field.

    fieldname could be in form of data__field, in which case we turn it into a lookup for data['field']. This is
    useful for grouping on a JSONField.
    """
    # Start with an empty list for accumulation
    current_group = []
    current_value = None
    attr, lookup_key = fieldname.split("__")

    for instance in queryset.order_by(fieldname).iterator(chunk_size=5000):
        if current_value is None:
            current_value = getattr_with_lookup_key(instance, attr, lookup_key)

        if getattr_with_lookup_key(instance, attr, lookup_key) != current_value:
            # New value encountered; process the current group
            yield current_group
            current_group = []  # Reset the accumulation
            current_value = getattr_with_lookup_key(instance, attr, lookup_key)

        # Add the instance to the current group
        current_group.append(instance)

    # Process the last group if it's not empty
    if current_group:
        yield current_group
