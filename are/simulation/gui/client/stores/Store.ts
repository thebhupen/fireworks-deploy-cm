// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
// 
// This source code is licensed under the terms described in the LICENSE file in
// the root directory of this source tree.


import { useEffect, useState } from "react";


export class Store<T> {
    private state: T
    private subscribers: Set<(state: T) => void>

    constructor({ initialState }: { initialState: T }) {
        this.state = initialState
        this.subscribers = new Set();
    }

    getState() {
        return this.state
    }

    subscribe(callback: (state: T) => void) {
        callback(this.state)
        this.subscribers.add(callback)

        return () => {
            this.subscribers.delete(callback)
        }
    }

    emit(state: T) {
        this.state = state

        for (const callback of this.subscribers) {
            callback(state)
        }
    }
}

export function useStore<T>(store: Store<T>): T {
    const [state, setState] = useState(store.getState())

    useEffect(() => {
        return store.subscribe(setState)
    }, [store])

    return state
}
