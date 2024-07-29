import streamlit as st
import requests
import pandas as pd
import altair as alt

# Define the Streamlit app
def app():
    st.title('MEV Value Dashboard')

    # Input fields for block heights
    initial_block_height = st.number_input('Initial Block Height', min_value=0, value=20510255)
    final_block_height = st.number_input('Final Block Height', min_value=0, value=20510258)

    if st.button('Get Data'):
        # Call the first API
        mev_api_url = f"https://dydx.observatory.zone/api/v1/raw_mev?limit=500000&from_height={initial_block_height}&to_height={final_block_height}&with_block_info=True"
        mev_response = requests.get(mev_api_url)
        mev_data = mev_response.json()

        # Parse the JSON response from the first API
        mev_datapoints = mev_data.get('datapoints', [])

        # Create a DataFrame for MEV data
        mev_df = pd.DataFrame(mev_datapoints)

        if not mev_df.empty:
            # Convert data types for MEV DataFrame
            mev_df['value'] = mev_df['value'].astype(float)
            mev_df['height'] = mev_df['height'].astype(int)

            # Add a new column for MEV value in millions of dollars
            mev_df['MEV value ($)'] = mev_df['value'] / 10**6

            # Call the second API
            validator_api_url = "https://dydx.observatory.zone/api/v1/validator"
            validator_response = requests.get(validator_api_url)
            validator_data = validator_response.json()

            # Parse the JSON response from the second API
            validators = validator_data.get('validators', [])

            # Create a DataFrame for Validator data
            validator_df = pd.DataFrame(validators)

            # Merge the MEV DataFrame with the Validator DataFrame on the proposer/pubkey
            merged_df = pd.merge(mev_df, validator_df, left_on='proposer', right_on='pubkey', how='left')

            # Create the vertical bar chart
            vertical_chart = alt.Chart(merged_df).mark_bar().encode(
                x=alt.X('height:O', title='Block Height'),
                y=alt.Y('MEV value ($):Q', title='MEV value ($)'),
                tooltip=[alt.Tooltip('height:O', title='Block Height'), 
                         alt.Tooltip('MEV value ($):Q', title='MEV value ($)'),
                         alt.Tooltip('moniker:N', title='Block Proposer')]
            ).properties(
                title='MEV Value by Block Height'
            )

            st.altair_chart(vertical_chart, use_container_width=True)

            # Get the top 15 blocks by MEV value
            top15_df = merged_df.nlargest(15, 'MEV value ($)')

            # Order the top 15 DataFrame by MEV value in descending order
            top15_df = top15_df.sort_values(by='MEV value ($)', ascending=False)

            # Create the horizontal bar chart
            horizontal_chart = alt.Chart(top15_df).mark_bar().encode(
                x=alt.X('MEV value ($):Q', title='MEV value ($)'),
                y=alt.Y('height:O', title='Block Height', sort='-x'),
                tooltip=[alt.Tooltip('height:O', title='Block Height'), 
                         alt.Tooltip('MEV value ($):Q', title='MEV value ($)'),
                         alt.Tooltip('moniker:N', title='Block Proposer')]
            ).properties(
                title='Top 15 Block Heights with Highest MEV Value'
            )

            st.altair_chart(horizontal_chart, use_container_width=True)
        else:
            st.write("No data available for the given block heights.")

# Run the app
if __name__ == '__main__':
    app()
