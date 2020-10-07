#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

import numpy as np
from pandas import DataFrame
from sklearn.preprocessing import OneHotEncoder
from mlos.Spaces import Point, CategoricalDimension, DiscreteDimension, Hypergrid, SimpleHypergrid
from mlos.Spaces.HypergridAdapters.HypergridAdapter import HypergridAdapter
from mlos.Spaces.HypergridAdapters.HierarchicalToFlatHypergridAdapter import HierarchicalToFlatHypergridAdapter
from mlos.Spaces.HypergridAdapters.CategoricalToDiscreteHypergridAdapter import CategoricalToDiscreteHypergridAdapter


class CategoricalToOneHotEncodedHypergridAdapter(HypergridAdapter):
    """ Maps values in categorical dimensions into values in OneHotEncoded dimensions using:
        https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html,
        which will be referred to as sklearn's OHE.

        Parameters
        ----------
        merge_all_categorical_dimensions: bool
            If True, sklearn's OHE will be applied to the cross product of all categorical levels in the adaptee space.
            If False, sklearn's OHE will be applied individually to each categorical dimension in the adaptee space.
            Default=False.
        drop: {None, 'first', 'if_binary'}
            Argument passed to sklearn's OHE with same argument name.
            Default=None.
        dtype: number type
            Argument passed to sklearn's OHE with same argument name.
            Default=np.int.

        The following sklearn OHE arguments are not supported or are restricted:
        categories: Not supported since the levels a categorical can assume are those specified by the adaptee CategoricalDimension categories.
        drop: Not supporting sklearn's OHE drop argument as a array-like of shape (n_features,).
        sparse: Not exposed in the adapter since the adapter maintains the OHE instances.
        handle_unknown: This adapter will always set sklearn's OHE instantiation argument handle_unknown='error'.

    """

    def __init__(self,
                 adaptee: Hypergrid,
                 merge_all_categorical_dimensions: bool = False,
                 drop: str = None,
                 dtype=np.int):
        if not HypergridAdapter.is_like_simple_hypergrid(adaptee):
            raise ValueError("Adaptee must implement a Hypergrid Interface.")

        HypergridAdapter.__init__(self, name=adaptee.name, random_state=adaptee.random_state)

        self._adaptee: Hypergrid = adaptee
        self._merge_all_categorical_dimensions = merge_all_categorical_dimensions
        self._one_hot_encoder_kwargs = {
            'drop': drop,
            'dtype': dtype,
            'sparse': False,
            'handle_unknown': 'error'
        }
        self._all_one_hot_encoded_target_dimension_names = []
        self._adaptee_to_target_data = {}
        self._target_to_adaptee_data = {}
        self._concatenation_delim = '___'
        self._merged_categorical_dimension_column_name = 'dimension_cross_product'
        self.ohe_target_column_suffix = '__ohe'
        #self._categories_per_dimension = []
        self._categorical_to_discrete_adapter = None
        self._target: Hypergrid = None
        self.is_adaptee_hierarchical = self._adaptee.is_hierarchical()

        if self.is_adaptee_hierarchical:
            self._adaptee = HierarchicalToFlatHypergridAdapter(adaptee=self._adaptee)

        # Since CategoricalDimension values may have different types within the same dimension,
        #  we pass the adaptee through the CategoricalToDiscrete adapter to move all value types to ints
        # Since this converts categorical dimensions to discrete dimensions, we remember the categorical dim names
        self._adaptee_dimension_names_to_transform = []
        for adaptee_dimension in self._adaptee.dimensions:
            if isinstance(adaptee_dimension, CategoricalDimension):
                self._adaptee_dimension_names_to_transform.append(adaptee_dimension.name)

        if any(isinstance(dimension, CategoricalDimension) for dimension in self._adaptee.dimensions):
            self._categorical_to_discrete_adapter = CategoricalToDiscreteHypergridAdapter(adaptee=self._adaptee)
            self._adaptee = self._categorical_to_discrete_adapter

        self._build_simple_hypergrid_target()

    @property
    def adaptee(self) -> Hypergrid:
        return self._adaptee

    @property
    def target(self) -> Hypergrid:
        return self._target

    def get_one_hot_encoded_column_names(self):
        return self._all_one_hot_encoded_target_dimension_names

    def _concatenate_dataframe_columns(self, df: DataFrame, columns_to_concatenate) -> DataFrame:
        return df[columns_to_concatenate].apply(lambda cat_row: self._concatenation_delim.join(cat_row.map(str)), axis=1)

    def _concatenate_string_list_values(self, row_values) -> str:
        return self._concatenation_delim.join(row_values)

    def _project_point(self, point: Point) -> Point:
        projected_point = Point()
        for dim_name, adaptee_dim_value in point:
            if dim_name in self._adaptee_dimension_names_to_transform:
                if self._merge_all_categorical_dimensions:
                    ohe_dict = self._adaptee_to_target_data[self._merged_categorical_dimension_column_name]
                    ohe_x = self._concatenate_string_list_values([str(point[dim_name]) for dim_name in self._adaptee_dimension_names_to_transform])
                else:
                    ohe_dict = self._adaptee_to_target_data[dim_name]
                    ohe_x = [str(point[dim_name])]
                ohe_x = np.array(ohe_x).reshape(-1, 1)
                target_values = ohe_dict['one_hot_encoder'].transform(ohe_x).tolist()[0]
                for i, target_value in enumerate(target_values):
                    target_name = ohe_dict['target_dims'][i]
                    projected_point[target_name] = target_value
            else:
                projected_point[dim_name] = adaptee_dim_value
        return projected_point

    def _unproject_point(self, point: Point) -> Point:
        unprojected_point = Point()
        for target_dim_name, target_dim_value in point:
            if target_dim_name in self._all_one_hot_encoded_target_dimension_names:
                adaptee_dim_names = []
                if self._merge_all_categorical_dimensions:
                    adaptee_dim_names = self._adaptee_dimension_names_to_transform
                    if any([adaptee_dim_name in unprojected_point for adaptee_dim_name in adaptee_dim_names]):
                        continue
                    ohe_dict = self._adaptee_to_target_data[self._merged_categorical_dimension_column_name]
                    target_names = ohe_dict['target_dims']
                    ohe_y = np.array([point[target_name] for target_name in target_names]).reshape(1, -1)
                    pre_split_adaptee_value = ohe_dict['one_hot_encoder'].inverse_transform(ohe_y)
                    adaptee_values = pre_split_adaptee_value[0][0].split(self._concatenation_delim)
                else:
                    adaptee_dim_name = self._target_to_adaptee_data[target_dim_name]
                    if adaptee_dim_name in unprojected_point:
                        continue
                    adaptee_dim_names.append(adaptee_dim_name)
                    ohe_dict = self._adaptee_to_target_data[adaptee_dim_name]
                    target_names = ohe_dict['target_dims']
                    ohe_y = np.array([point[target_name] for target_name in target_names]).reshape(1, -1)
                    adaptee_values = ohe_dict['one_hot_encoder'].inverse_transform(ohe_y)

                for i, adaptee_dim_name in enumerate(adaptee_dim_names):
                    if adaptee_dim_name in unprojected_point:
                        if self._merge_all_categorical_dimensions:
                            raise ValueError(
                                f'Attempting to set previously set adaptee dimension "{adaptee_dim_name}" is unexpected for hierarchical hypergrids.')
                        if not self._merge_all_categorical_dimensions and (i > 0):
                            raise ValueError(
                                f'Found more than one adaptee dimension "{adaptee_dim_name}" and this is unexpected for non-hierarchical hypergrids.')
                        continue
                    adaptee_value = adaptee_values[i]
                    unprojected_point[adaptee_dim_name] = int(adaptee_value[0])
            else:
                adaptee_dim_name = target_dim_name
                unprojected_point[adaptee_dim_name] = target_dim_value
        return unprojected_point

    def _project_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        if not in_place:
            df = df.copy(deep=True)

        columns_to_drop = []
        columns_to_transform = self._adaptee_dimension_names_to_transform
        if self._merge_all_categorical_dimensions:
            df[self._merged_categorical_dimension_column_name] = self._concatenate_dataframe_columns(df, columns_to_transform)
            columns_to_transform = [self._merged_categorical_dimension_column_name]
            columns_to_drop.extend(self._adaptee_dimension_names_to_transform)

        for adaptee_column_name in columns_to_transform:
            my_ohe = self._adaptee_to_target_data[adaptee_column_name]['one_hot_encoder']
            ohe_x = df[adaptee_column_name].map(str).to_numpy().reshape(-1, 1)
            my_ohe_target_columns = self._adaptee_to_target_data[adaptee_column_name]['target_dims']
            df[my_ohe_target_columns] = DataFrame(my_ohe.transform(ohe_x), index=df.index)
            columns_to_drop.append(adaptee_column_name)

        if columns_to_drop:
            df.drop(columns=columns_to_drop, inplace=True)
        return df

    def _unproject_dataframe(self, df: DataFrame, in_place=True) -> DataFrame:
        if not in_place:
            df = df.copy(deep=True)

        columns_to_drop = []
        if self._merge_all_categorical_dimensions:
            my_ohe_dict = self._adaptee_to_target_data[self._merged_categorical_dimension_column_name]
            target_columns_to_invert = my_ohe_dict['target_dims']
            my_ohe = my_ohe_dict['one_hot_encoder']
#            df[self._merged_categorical_dimension_column_name] = my_ohe.inverse_transform(df[target_columns_to_invert])
#            df[self._adaptee_dimension_names_to_transform] = df[self._merged_categorical_dimension_column_name]\
#                .str.split(self._concatenation_delim, expand=True)
            df[self._adaptee_dimension_names_to_transform] = my_ohe.inverse_transform(df[target_columns_to_invert]).astype(int)
            columns_to_drop.extend(target_columns_to_invert)
            columns_to_drop.append(self._merged_categorical_dimension_column_name)
        else:
            for adaptee_column_name in self._adaptee_dimension_names_to_transform:
                my_ohe_dict = self._adaptee_to_target_data[adaptee_column_name]
                target_columns_to_invert = my_ohe_dict['target_dims']
                my_ohe = my_ohe_dict['one_hot_encoder']
                df[adaptee_column_name] = my_ohe.inverse_transform(df[target_columns_to_invert]).astype(int)
                columns_to_drop.extend(target_columns_to_invert)

        if columns_to_drop:
            df.drop(columns=columns_to_drop, inplace=True)

        print('my _unproject_dataframe: ', df)

        # # invert the categorical to discrete adapter
        # if self._categorical_to_discrete_adapter is not None:
        #     df = self._categorical_to_discrete_adapter.unproject_dataframe(df)

        return df

    def _build_simple_hypergrid_target(self) -> None:
        """ Builds a SimpleHypergrid target for a SimpleHypergrid adaptee.

        :return:
        """

        self._target = SimpleHypergrid(
            name=self._adaptee.name,
            dimensions=None,
            random_state=self._adaptee.random_state
        )

        """ Details about construction of the target hypergrid:
           1) Moving non-categorical dimensions to target, while collecting needed info about adaptee categorical dimensions
           2) Since sklearn's OHE will handle both project and unproject dataframe transforms, prepare the OHE class.
              This requires constructing the 'categories' argument for OHE (all categorical dims or 1 cross product dim).
              The dimension's .linspace() method provides the order list of values but doesn't include possible np.NaN values,
               hence that list is augmented to include the string 'nan' which pandas.DataFrame.apply(map(str)) will produce from a np.NaN value.
              All values (output from CategoricalToDiscrete adapter are converted to strings prior to initializing the OHE object.
               This will allow the code to accommodate any missing values in the dataframes passed to .project_dataframe and .unproject_dataframe.
           3) If the cross product of all categorical dimensions have been requested, construct the cross product
        """

        categories_list_for_ohe_init = []
        for adaptee_dimension in self._adaptee.dimensions:
            if adaptee_dimension.name in self._adaptee_dimension_names_to_transform:
                """ conversion to str allows accommodation of np.NaN values in dataframes
                    np.NaN values will not appear in the .linspace() list but will be present in dataframes generated from hierarchical hypergrods.
                     So 'nan' is included to allow OHE to map np.NaNs in ._project_dataframe() and ._unproject_dataframe().
                    The value 'nan' is placed first in the list so the 'nan' x ... x 'nan' cross product value is first ([0]).
                     Since this value should never appear in hierarchical hypergrid derived dataframes, it is popped from
                     the categories when user specifies merge_all_categorical_dimensions==True.
                """
                expanded_categories = []
                if self.is_adaptee_hierarchical:
                    expanded_categories.append('nan')
                expanded_categories.extend([str(x) for x in adaptee_dimension.linspace()])
                categories_list_for_ohe_init.append(expanded_categories)

                if not self._merge_all_categorical_dimensions:
                    # do not need to encode the cross product of all categorical dimensions, sufficient info here to add target dimensions
                    self._adaptee_to_target_data[adaptee_dimension.name] = {
                        'target_dims': [],
                        'one_hot_encoder': OneHotEncoder(categories=[expanded_categories], **self._one_hot_encoder_kwargs),
                        'num_dummy_dims': None
                    }
                    temp_df_for_fit = DataFrame({adaptee_dimension.name: expanded_categories})
                    self._add_one_hot_encoded_dimensions(adaptee_dimension.name, temp_df_for_fit)
            else:
                self._target.add_dimension(adaptee_dimension.copy())

        if self._merge_all_categorical_dimensions:
            # harvested categories for each categorical dimension in single pass across all adaptee dimensions used to compute the cross product encoding here
            cross_product_categories = self._create_cross_product_categories(categories_list_for_ohe_init)
            self._adaptee_to_target_data[self._merged_categorical_dimension_column_name] = {
                'target_dims': [],
                'one_hot_encoder': OneHotEncoder(categories=[cross_product_categories], **self._one_hot_encoder_kwargs),
                'num_dummy_dims': None
            }
            temp_df_for_fit = DataFrame({self._merged_categorical_dimension_column_name: cross_product_categories})
            self._add_one_hot_encoded_dimensions(self._merged_categorical_dimension_column_name, temp_df_for_fit)

    def _add_one_hot_encoded_dimensions(self, adaptee_dimension_name, temp_df_for_fit: DataFrame) -> None:
        my_target_data = self._adaptee_to_target_data[adaptee_dimension_name]
        my_ohe_output = my_target_data['one_hot_encoder'].fit_transform(temp_df_for_fit)
        num_dummy_dims = my_ohe_output.shape[1]
        my_target_data['num_dummy_dims'] = my_ohe_output.shape[1]
        for i in range(num_dummy_dims):
            target_dim_name = f'{adaptee_dimension_name}{self.ohe_target_column_suffix}{i}'
            my_target_data['target_dims'].append(target_dim_name)
            self._target_to_adaptee_data[target_dim_name] = adaptee_dimension_name
            self._target.add_dimension(DiscreteDimension(name=target_dim_name, min=0, max=1))
            self._all_one_hot_encoded_target_dimension_names.append(target_dim_name)

    def _create_cross_product_categories(self, categories_per_dimension) -> []:
        num_categorical_dims = len(categories_per_dimension)
        cross_product = np.array(np.meshgrid(*categories_per_dimension)).T.reshape(-1, num_categorical_dims)
        temp_df = DataFrame(cross_product)
        temp_df['concatenated_levels'] = self._concatenate_dataframe_columns(temp_df, temp_df.columns.values)
        concatenated_levels = temp_df['concatenated_levels'].values.tolist()

        # expect first element arises from 'nan' x ... x 'nan' which cannot appear in hierarchical hypergrids,
        #  so popping this before returning the cross product list
        if self.is_adaptee_hierarchical and num_categorical_dims > 1:
            all_nans = self._concatenation_delim.join(['nan'] * num_categorical_dims)
            should_be_all_nans = concatenated_levels.pop(0)
            if should_be_all_nans != all_nans:
                raise ValueError('Failed to find cross product of nan values when constructing OneHotEncoding with merge_all_categorical_dimensions==True')

        return concatenated_levels
