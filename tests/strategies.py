from datetime import timezone, datetime
from hypothesis import given, strategies as st
from minimono.models import (
    Account,
    Transaction,
    User,
    Statement,
    CurrencyExchange,
    HeadersPrivate,
    TxBucket,
    StatementReq,
)

b_tx_bucket = st.builds(
    TxBucket,
    transactions=st.lists(st.builds(Transaction))
)

b_non_empty_statement = st.builds(
    Statement,
    transactions=st.lists(
        st.builds(Transaction),
        min_size=2
    )
    )

b_any_model = st.one_of(
        st.builds(
            Account,
            cached_statement=st.dictionaries(
                st.text(min_size=1, max_size=20),
                b_tx_bucket,
            ),
        ),
        st.builds(Transaction),
        st.builds(User),
        b_non_empty_statement,
        st.builds(CurrencyExchange),
        st.builds(HeadersPrivate),
        st.builds(
            StatementReq,
            from_=st.one_of(st.datetimes(min_value=datetime(2017, 11, 1,), timezones=st.sampled_from([timezone.utc,]), allow_imaginary=False), st.none()),
            to_=st.one_of(st.datetimes(min_value=datetime(2017, 11, 2,), timezones=st.sampled_from([timezone.utc,]), allow_imaginary=False), st.none()),
    )
    )