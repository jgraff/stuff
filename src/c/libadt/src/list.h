#ifndef _ADT_LIST_H
#define _ADT_LIST_H

/*******************************************************************************
 * Single linked list
 */

struct ADT_sl_node {
  void *data;
  struct ADT_sl_node *next;
};

struct ADT_sl_list {
  struct ADT_sl_node *head;
  struct ADT_sl_node *tail;
  unsigned int len;
};

void ADT_sl_list_init(struct ADT_sl_list *);
void ADT_sl_list_destroy(struct ADT_sl_list *, void (*destroy)(void *));
int ADT_sl_list_push(struct ADT_sl_list *, void *);
void ADT_sl_list_pop(struct ADT_sl_list *, void **);
int ADT_sl_list_append(struct ADT_sl_list *, void *);
int ADT_sl_list_insert_after(struct ADT_sl_list *, struct ADT_sl_node *, void *);
void ADT_sl_list_remove_after(struct ADT_sl_list *, struct ADT_sl_node *, void **);
unsigned int ADT_sl_list_length(struct ADT_sl_list *);
#define ADT_sl_list_enqueue(list, data) ADT_sl_list_append(list, data)
#define ADT_sl_list_dequeue(list, data) ADT_sl_list_pop(list, data)


#endif
