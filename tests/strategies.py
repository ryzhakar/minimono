from datetime import timezone, datetime
from hypothesis import given, strategies as st
from minimono.API.models import (
    Account,
    Transaction,
    UserInfoResp,
    StatementResp,
    CurrencyInfo,
    HeadersPrivate,
    TxBucket,
    StatementReq,
)

b_tx_bucket = st.builds(
    TxBucket,
    transactions=st.lists(st.builds(Transaction))
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
        st.builds(UserInfoResp),
        st.builds(StatementResp),
        st.builds(CurrencyInfo),
        st.builds(HeadersPrivate),
        st.builds(
            StatementReq,
            from_=st.one_of(st.datetimes(min_value=datetime(2017, 11, 1,), timezones=st.sampled_from([timezone.utc,]), allow_imaginary=False), st.none()),
            to_=st.one_of(st.datetimes(min_value=datetime(2017, 11, 2,), timezones=st.sampled_from([timezone.utc,]), allow_imaginary=False), st.none()),
    )
    )