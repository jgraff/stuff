#include <stdlib.h>
#include <assert.h>
#include "list.h"
#ifdef DMALLOC
  #include "dmalloc.h"
#endif

/*
 * Return a new initialized Single Linked List.
 * Pre: list is a pointer to a newly created ADT_sl_list.
 * Post: list's head and tail will be set to NULL. The length
 * list will be zero.
 */
void
ADT_sl_list_init(struct ADT_sl_list *list)
{
  list->head = NULL;
  list->tail = NULL;
  list->len = 0;
}

/*
 * Remove all items from list and call the designated destory fn
 * to free list data.
 * Pre: list must be a pointer to an initialized ADT_sl_list structure,
 *      and destory must be valid function for freeing list data.
 * Post: list nodes are all destoryed. list head and tail are set
 *       to NULL.
 */
void
ADT_sl_list_destroy(struct ADT_sl_list *list, void (*destroy)(void *))
{
  void *data = NULL;

  while (ADT_sl_list_length(list) != 0) {
    ADT_sl_list_pop(list, (void *)&data);
    (*destroy)(data);
  }
  list->head = NULL;
  list->tail = NULL;
}

/*
 * Insert data at the head of list.
 * Pre: list must be a pointer to an initialized ADT_sl_list structure.
 * Post: data will be located in a node at the head of list, and the
 *       list length will be increased by one.
 * Returns: 0 on success or -1 on a malloc error.
 *
 */
int
ADT_sl_list_push(struct ADT_sl_list *list, void *data)
{
  struct ADT_sl_node *node = (struct ADT_sl_node *)malloc(sizeof(struct ADT_sl_node));

  if (node == NULL)
    return -1;
  if (ADT_sl_list_length(list) == 0) {
    list->tail = node;
  }
  node->data = data;
  node->next = list->head;
  list->head = node;
  list->len++;
  return 0;
}

/*
 * Remove data from the head of list.
 * Pre: list must be a pointer to an initialized ADT_sl_list structure.
 * Post: The node at the head of list is destroyed and data points
 *       to the data previously held in node. List length is reduced
 *       by one.
 * Note: This routine will abort and die if an attempt is made to
 *       pop from an empty list.
 */
void
ADT_sl_list_pop(struct ADT_sl_list *list, void **data)
{
  struct ADT_sl_node *node;

  assert(ADT_sl_list_length(list) != 0);
  node = list->head;
  *data = list->head->data;
  list->head = node->next;
  list->len--;
  free(node);
  node = NULL;
}

/*
 * Insert data to the end of list.
 * Pre: list must be a pointer to an initialized ADT_sl_list structure.
 * Post: data will be contained in a node at the end of list. List
 *       length will be increased by one.
 * Returns: 0 on success, or -1 on malloc failure.
 *
 */
int
ADT_sl_list_append(struct ADT_sl_list *list, void *data)
{
  struct ADT_sl_node *node = NULL;

  if (ADT_sl_list_length(list) == 0) {
    ADT_sl_list_push(list, data);
  } else {
    node = (struct ADT_sl_node *)malloc(sizeof(struct ADT_sl_node));
    if (node == NULL)
      return -1;
    node->data = data;
    node->next = NULL;
    list->tail->next = node;
    list->tail = node;
    list->len++;
  }
  return 0;
}

/*
 * Insert data into list immediately after loc.
 * Pre: list must be a pointer to an initialized ADT_sl_list structure, and loc
 *      *must* be a pointer to an actual node.
 * Returns: 0 on success or -1 on malloc failure.
 *
 */
int
ADT_sl_list_insert_after(struct ADT_sl_list *list, struct ADT_sl_node *loc, void *data)
{
  struct ADT_sl_node *node = (struct ADT_sl_node *)malloc(sizeof(struct ADT_sl_node));

  if (node == NULL)
    return -1;
  if (loc == list->tail) {
    list->tail = node;
  }
  node->data = data;
  node->next = loc->next;
  loc->next = node;
  list->len++;
  return 0;
}

/*
 * Remove the node, immediately after loc, from the list. Upon completion data
 * points to the removed node's data.
 * Pre: list must be a pointer to an initialized ADT_sl_list structure, and loc
 *      *must* be a pointer to an actual node.
 * Notes: This routine will abort and die if loc points to the last node in
 *        list (tail). i.e. There is nothing to remove.
 */
void
ADT_sl_list_remove_after(struct ADT_sl_list *list, struct ADT_sl_node *loc, void **data)
{
  struct ADT_sl_node *ptr;
  assert(loc != list->tail);
  ptr = loc->next;
  *data = loc->next->data;
  loc->next = loc->next->next;
  free(ptr);
  list->len--;
}

unsigned int
ADT_sl_list_length(struct ADT_sl_list *list)
{
  return list->len;
}
