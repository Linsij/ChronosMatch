
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

from libc.stdlib cimport malloc, free

cdef struct Order:
    long order_id
    long price
    long quantity
    long sequence
    int side

cdef class OrderBook:
    cdef Order* bids
    cdef Order* asks
    cdef int bid_count
    cdef int ask_count
    cdef int capacity
    cdef long sequence

    def __cinit__(self, int capacity=100000):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.bid_count = 0
        self.ask_count = 0
        self.sequence = 0

        self.bids = <Order*>malloc(capacity * sizeof(Order))
        self.asks = <Order*>malloc(capacity * sizeof(Order))

        if self.bids == NULL or self.asks == NULL:
            free(self.bids)
            free(self.asks)
            self.bids = NULL
            self.asks = NULL
            raise MemoryError()

    def __dealloc__(self):
        free(self.bids)
        free(self.asks)

    cdef int find_best_bid(self) noexcept nogil:
        cdef int i, best = -1

        for i in range(self.bid_count):
            if best == -1 or self.bids[i].price > self.bids[best].price:
                best = i
            elif self.bids[i].price == self.bids[best].price:
                if self.bids[i].sequence < self.bids[best].sequence:
                    best = i

        return best

    cdef int find_best_ask(self) noexcept nogil:
        cdef int i, best = -1

        for i in range(self.ask_count):
            if best == -1 or self.asks[i].price < self.asks[best].price:
                best = i
            elif self.asks[i].price == self.asks[best].price:
                if self.asks[i].sequence < self.asks[best].sequence:
                    best = i

        return best

    cdef long execute_match(
        self,
        Order* incoming,
        Order* resting,
        long* execution_price
    ) noexcept nogil:

    cdef long traded

        if incoming.quantity < resting.quantity:
            traded = incoming.quantity
        else:
            traded = resting.quantity

        execution_price[0] = resting.price

        incoming.quantity -= traded
        resting.quantity -= traded

        return traded

    def add_order(self, long order_id, long price,
                  long quantity, int side):
        cdef Order order
        cdef int best, i
        cdef long traded
        cdef long execution_price
        cdef list trades = []

        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")

        if side != 0 and side != 1:
            raise ValueError("Side must be 0 (BUY) or 1 (SELL)")

        order.order_id = order_id
        order.price = price
        order.quantity = quantity
        order.side = side
        order.sequence = self.sequence
        self.sequence += 1

        while order.quantity > 0:
            if side == 0:
                with nogil:
                    best = self.find_best_ask()

                if best == -1 or self.asks[best].price > price:
                    break

                with nogil:
                traded = self.execute_match(
                &order,
                &self.asks[best],
                &execution_price
                )
                trades.append((
                    order_id,
                    self.asks[best].order_id,
                    execution_price,
                    traded
                ))

                if self.asks[best].quantity == 0:
                    for i in range(best, self.ask_count - 1):
                        self.asks[i] = self.asks[i + 1]
                    self.ask_count -= 1

            else:
                with nogil:
                    best = self.find_best_bid()

                if best == -1 or self.bids[best].price < price:
                    break

                traded = min(order.quantity, self.bids[best].quantity)
                execution_price = self.bids[best].price
                order.quantity -= traded
                self.bids[best].quantity -= traded

                trades.append((
                    self.bids[best].order_id,
                    order_id,
                    execution_price,
                    traded
                ))

                if self.bids[best].quantity == 0:
                    for i in range(best, self.bid_count - 1):
                        self.bids[i] = self.bids[i + 1]
                    self.bid_count -= 1

        if order.quantity > 0:
            if side == 0:
                if self.bid_count >= self.capacity:
                    raise OverflowError("Bid book is full")
                self.bids[self.bid_count] = order
                self.bid_count += 1
            else:
                if self.ask_count >= self.capacity:
                    raise OverflowError("Ask book is full")
                self.asks[self.ask_count] = order
                self.ask_count += 1

        return trades

    def top_of_book(self):
        cdef int bid, ask

        with nogil:
            bid = self.find_best_bid()
            ask = self.find_best_ask()

        return {
            "best_bid": self.bids[bid].price if bid >= 0 else None,
            "best_ask": self.asks[ask].price if ask >= 0 else None,
            "bid_count": self.bid_count,
            "ask_count": self.ask_count,
        }
