// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.

const USERNAME_KEY = "username";

const userInfoStorage = {
  setLogin: (username: string) => {
    localStorage.setItem(USERNAME_KEY, username);
  },
  getLogin: () => {
    const username = localStorage.getItem(USERNAME_KEY);
    return username;
  },
  clearLogin: () => {
    localStorage.removeItem(USERNAME_KEY);
  },
};
export default userInfoStorage;
