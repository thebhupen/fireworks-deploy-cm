# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import strawberry

from are.simulation.gui.server.graphql.mutation import Mutation
from are.simulation.gui.server.graphql.query import Query
from are.simulation.gui.server.graphql.subscription import Subscription

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
